import asyncio
import json
import os

from fastapi import HTTPException
from groq import Groq

_client: Groq | None = None

MODEL = "llama-3.3-70b-versatile"

STYLES = {
    "dark": """- Dark theme: background #0a0a14, cards on #111127, accent color — pick ONE fitting the business (purple #6366f1, cyan #06b6d4, emerald #10b981, orange #f97316, etc.)
- Typography: use Google Fonts (import in <style>) — Inter or Plus Jakarta Sans
- Subtle animated background: 2-3 blurred color orbs (position:fixed, blur:100px, opacity:0.12, slow float animation)
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


def _get_client() -> Groq:
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise HTTPException(status_code=503, detail="GROQ_API_KEY is not configured")
        _client = Groq(api_key=api_key)
    return _client


async def call_groq(prompt: str, timeout: float, max_tokens: int = 4096) -> str:
    client = _get_client()
    loop = asyncio.get_running_loop()
    try:
        response = await asyncio.wait_for(
            loop.run_in_executor(None, lambda: client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=max_tokens,
            )),
            timeout=timeout
        )
        text = response.choices[0].message.content
        if not text:
            raise HTTPException(status_code=502, detail="AI returned an empty response")
        return text.strip()
    except TimeoutError:
        raise HTTPException(status_code=504, detail=f"AI did not respond within {int(timeout)} seconds")
    except HTTPException:
        raise
    except Exception as e:
        if "429" in str(e) or "rate limit" in str(e).lower():
            raise HTTPException(
                status_code=429,
                detail="Daily AI quota reached. Please try again tomorrow.",
            )
        raise HTTPException(status_code=502, detail=f"AI error: {str(e)}")


def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else ""
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


async def clarify_questions(business_name: str, description: str) -> list[str]:
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

    text = await call_groq(prompt, timeout=30.0, max_tokens=512)
    text = _strip_fences(text)

    try:
        questions = json.loads(text)
        if not isinstance(questions, list) or len(questions) == 0:
            raise ValueError
    except (json.JSONDecodeError, ValueError):
        raise HTTPException(status_code=502, detail="AI returned an invalid format")
    return questions


async def generate_landing(
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

    prompt = f"""You are an expert web designer. Create a stunning, complete single-file HTML landing page.

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
- On page load: hero elements fade in with translateY (staggered, use animation-delay)
- On scroll: sections animate in using IntersectionObserver + CSS class toggle (add class "visible" to trigger opacity:0→1 + translateY:20px→0, transition 0.6s)
- FAQ accordion: smooth max-height transition

=== TECHNICAL ===
- Single HTML file, all CSS in <style>, all JS in <script>
- Fully responsive (mobile-first, CSS Grid + Flexbox)
- No external JS libraries (vanilla JS only)
- All text content (headings, copy, testimonials, FAQ) written in {language}, generated to fit the specific business
- Return ONLY the HTML code, no markdown, no explanation, no ```html wrapper"""

    text = await call_groq(prompt, timeout=90.0, max_tokens=8192)
    return _strip_fences(text)
