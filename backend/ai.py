import asyncio
import json
import logging
import os
import time

from fastapi import HTTPException
from groq import AsyncGroq

logger = logging.getLogger("landing_studio.ai")

_client: AsyncGroq | None = None

MODELS = {
    "scout": "meta-llama/llama-4-scout-17b-16e-instruct",
    "gpt-oss": "openai/gpt-oss-120b",
}
# Groq free tier caps tokens-per-minute per request (8000 for gpt-oss-120b),
# so the output budget must leave room for the ~1k-token prompt
GENERATION_MAX_TOKENS = {
    "scout": 16384,
    "gpt-oss": 6000,
}
DEFAULT_MODEL_KEY = os.getenv("GROQ_MODEL", "gpt-oss")


def generation_max_tokens(model_key: str) -> int:
    return GENERATION_MAX_TOKENS.get(model_key or DEFAULT_MODEL_KEY, 8192)

STYLES = {
    "dark": """- Dark theme: background #0a0a14, cards on #111127, accent color — pick ONE fitting the business (purple #6366f1, cyan #06b6d4, emerald #10b981, orange #f97316, etc.)
- Typography: use Google Fonts (import in <style>) — Inter or Plus Jakarta Sans
- Subtle background depth: 2-3 blurred color orbs (position:fixed, blur:100px, opacity:0.12, static — no animation)
- Cards: glassmorphism style (background rgba white 4%, border rgba white 8%, backdrop-filter blur 10px, border-radius 16px)
- Buttons: gradient fill, border-radius 10px, hover: lift + glow shadow""",
    "light": """- Light minimal theme: background #fafafa, white cards with subtle border #e5e5e5 and soft shadow, near-black text #171717, ONE muted accent color fitting the business (deep blue #1d4ed8, forest #15803d, terracotta #c2410c, etc.)
- Typography: use Google Fonts (import in <style>) — Inter or Source Sans 3, generous whitespace, large line-height
- No decorative background effects — clean and airy, lots of negative space
- Cards: white, border-radius 12px, 1px solid border, shadow only on hover
- Buttons: solid accent fill, border-radius 8px, hover: slightly darker shade""",
    "vibrant": """- Bold vibrant theme: white or very light background, large saturated gradient accents (pick a 2-color gradient fitting the business: violet→pink, blue→cyan, orange→red, etc.)
- Typography: use Google Fonts (import in <style>) — Poppins or Outfit, extra-bold headlines (font-weight 800), oversized hero text
- Decorative shapes: 2-3 large gradient blobs or tilted gradient sections as section backgrounds
- Cards: white with bold colored top border or gradient border, border-radius 20px, playful hover scale(1.03)
- Buttons: gradient fill with strong shadow in accent color, border-radius 999px (pill shape)""",
}


def resolve_model(model_key: str) -> str:
    key = model_key or DEFAULT_MODEL_KEY
    if key not in MODELS:
        raise HTTPException(status_code=400, detail=f"Unknown model: {key}")
    return MODELS[key]


def _get_client() -> AsyncGroq:
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise HTTPException(status_code=503, detail="GROQ_API_KEY is not configured")
        _client = AsyncGroq(api_key=api_key)
    return _client


def _map_error(e: Exception) -> HTTPException:
    if "429" in str(e) or "rate limit" in str(e).lower():
        return HTTPException(
            status_code=429,
            detail="Daily AI quota reached. Please try again tomorrow.",
        )
    return HTTPException(status_code=502, detail=f"AI error: {str(e)}")


async def call_groq(prompt: str, timeout: float, max_tokens: int = 4096, model_key: str = "") -> str:
    client = _get_client()
    model = resolve_model(model_key)
    started = time.monotonic()
    try:
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=max_tokens,
            ),
            timeout=timeout,
        )
        text = response.choices[0].message.content
        if not text:
            raise HTTPException(status_code=502, detail="AI returned an empty response")
        logger.info("groq call model=%s duration=%.1fs chars=%d", model, time.monotonic() - started, len(text))
        return text.strip()
    except TimeoutError:
        raise HTTPException(status_code=504, detail=f"AI did not respond within {int(timeout)} seconds")
    except HTTPException:
        raise
    except Exception as e:
        raise _map_error(e)


async def stream_groq(prompt: str, max_tokens: int | None = None, model_key: str = ""):
    """Yields text chunks from a streaming Groq completion."""
    client = _get_client()
    model = resolve_model(model_key)
    if max_tokens is None:
        max_tokens = generation_max_tokens(model_key)
    started = time.monotonic()
    total = 0
    try:
        stream = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=max_tokens,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content if chunk.choices else None
            if delta:
                total += len(delta)
                yield delta
        logger.info("groq stream model=%s duration=%.1fs chars=%d", model, time.monotonic() - started, total)
    except Exception as e:
        raise _map_error(e)


def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else ""
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


_REVEAL_FAILSAFE = (
    '<noscript><style>section.reveal{opacity:1!important;transform:none!important;}</style></noscript>'
    '<script>addEventListener("load",function(){setTimeout(function(){'
    'document.querySelectorAll("section.reveal:not(.visible)").forEach('
    'function(s){s.classList.add("visible")})},1200)})</script>'
)


def _inject_reveal_failsafe(html: str) -> str:
    """Guarantee reveal-animated sections become visible even if JS/observer fails."""
    idx = html.lower().rfind("</html>")
    if idx == -1:
        return html + _REVEAL_FAILSAFE
    return html[:idx] + _REVEAL_FAILSAFE + html[idx:]


def finalize_html(text: str) -> str | None:
    """Strip fences and validate completeness. Returns None when the HTML is unusable."""
    html = _strip_fences(text)
    lower = html.lower()
    if "<html" not in lower or not lower.rstrip().endswith("</html>"):
        return None
    if len(html) < 2000:
        return None
    if not lower.startswith("<!doctype"):
        html = "<!DOCTYPE html>\n" + html
    return _inject_reveal_failsafe(html)


async def clarify_questions(business_name: str, description: str, model_key: str = "") -> list[str]:
    prompt = f"""You are a landing page designer. A client wants a page for their business and you need to understand the details.

Business: {business_name}
Description: {description}

Ask exactly 5 clarifying questions in English. The questions must cover:
1. Target audience (who the customers are, age, needs)
2. Color palette or style preferences (dark/light, specific colors, mood)
3. The main action a visitor should take (book, buy, call, etc.)
4. Which sections or blocks matter (pricing, portfolio, testimonials, team, etc.)
5. Tone and character of the site (serious / dynamic / minimal / premium, etc.)

Return ONLY a JSON array of 5 strings. No explanations. Format:
["Question 1?", "Question 2?", "Question 3?", "Question 4?", "Question 5?"]"""

    text = await call_groq(prompt, timeout=30.0, max_tokens=1024, model_key=model_key)
    text = _strip_fences(text)

    try:
        questions = json.loads(text)
        if not isinstance(questions, list) or len(questions) == 0:
            raise ValueError
    except (json.JSONDecodeError, ValueError):
        raise HTTPException(status_code=502, detail="AI returned an invalid format")
    return questions


def generate_prompt(
    business_name: str,
    description: str,
    answers: str,
    style: str,
    language: str,
) -> str:
    style_block = STYLES.get(style, STYLES["dark"])

    answers_block = ""
    if answers.strip():
        answers_block = f"\n\nAdditional details from the client (answers to clarifying questions):\n{answers}"

    return f"""You are an expert web designer. Create a stunning, complete single-file HTML landing page.

Business name: {business_name}
Business description: {description}{answers_block}

=== DESIGN STYLE ===
{style_block}

=== REQUIRED SECTIONS (in this order) ===

1. NAVIGATION — logo (business name) left, 2-3 nav links right, sticky top, backdrop-blur background
2. HERO — large headline (split into 2 lines, gradient text), subheadline (1-2 sentences describing value), primary CTA button + secondary ghost button, hero visual (CSS-only decorative element — glowing rings or abstract shape)
3. FEATURES — "why choose us" heading, 3 feature cards in a row (icon emoji + title + description), cards have hover:translateY(-4px) transition
4. TESTIMONIALS — heading, 3 testimonial cards (quote text, star rating ★★★★★, name + role — all AI-generated fitting the business), cards in a row
5. FAQ — heading, 5 questions with answers relevant to the business, accordion behavior (click to expand/collapse) implemented in vanilla JS
6. CONTACT — heading, centered form: name input + email input + message textarea + submit button, form styled as a card matching the design style
7. FOOTER — business name, short tagline, copyright 2026

=== ANIMATIONS ===
- On page load: hero elements fade in with translateY (staggered via animation-delay, with `animation-fill-mode: both`). CRITICAL: the hero elements' base CSS must NOT contain `opacity: 0` — the hidden state must exist ONLY inside the keyframes' `from` block, so the elements stay visible after the animation ends
- On scroll: sections animate in. CRITICAL — content must be visible even if JS fails, so use exactly this progressive-enhancement pattern:
  * Do NOT put any hiding class (opacity:0) in the HTML markup itself
  * JS on DOMContentLoaded adds class "reveal" to each section, then IntersectionObserver adds class "visible" when the section enters the viewport (threshold 0.15) and unobserves it — never remove the class afterwards
  * CSS: `section.reveal {{ opacity: 0; transform: translateY(20px); transition: opacity .6s, transform .6s; }}` and `section.reveal.visible {{ opacity: 1; transform: none; }}` (the .visible rule must come after .reveal)
- FAQ accordion: smooth max-height transition

=== TECHNICAL ===
- Single HTML file, all CSS in <style>, all JS in <script>
- Set `color-scheme` on :root matching the page background (dark or light) so native scrollbars and form controls match the theme; also style the scrollbar to fit the design (thin, rounded semi-transparent thumb, transparent track) via `scrollbar-width`/`scrollbar-color` and `::-webkit-scrollbar*`
- Fully responsive (mobile-first, CSS Grid + Flexbox)
- No external JS libraries (vanilla JS only)
- Never put class="reveal" or opacity:0 directly in section markup — define the reveal hidden state only inside <style>/JS, so content stays visible if scripts fail
- All text content (headings, copy, testimonials, FAQ) written in {language}, generated to fit the specific business
- Return ONLY the HTML code, no markdown, no explanation, no ```html wrapper"""


RETRY_SUFFIX = "\n\nIMPORTANT: Your previous attempt was incomplete. Return the COMPLETE HTML document from <!DOCTYPE html> to </html> with nothing cut off."


async def generate_landing(
    business_name: str,
    description: str,
    answers: str,
    style: str,
    language: str,
    model_key: str = "",
) -> str:
    prompt = generate_prompt(business_name, description, answers, style, language)
    max_tokens = generation_max_tokens(model_key)

    text = await call_groq(prompt, timeout=120.0, max_tokens=max_tokens, model_key=model_key)
    html = finalize_html(text)
    if html is not None:
        return html

    logger.warning("generation invalid (len=%d), retrying once", len(text))
    text = await call_groq(prompt + RETRY_SUFFIX, timeout=120.0, max_tokens=max_tokens, model_key=model_key)
    html = finalize_html(text)
    if html is None:
        raise HTTPException(status_code=502, detail="AI returned an incomplete page twice. Please try again.")
    return html
