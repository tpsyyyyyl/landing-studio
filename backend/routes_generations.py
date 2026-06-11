import io
import json
import re
import zipfile
from datetime import datetime, time, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from . import ai
from .auth import DEMO_EMAIL, get_current_user
from .database import get_db
from .models import Generation, User

router = APIRouter(prefix="/api", tags=["generations"])

DAILY_LIMIT = 20
DAILY_LIMIT_DEMO = 5


class ClarifyRequest(BaseModel):
    business_name: str
    description: str
    model: str = ""


class GenerateRequest(BaseModel):
    business_name: str
    description: str
    answers: str = ""
    style: str = "dark"
    language: str = "English"
    model: str = ""


def _summary(g: Generation) -> dict:
    return {
        "id": g.id,
        "business_name": g.business_name,
        "description": g.description,
        "style": g.style,
        "language": g.language,
        "model": g.model,
        "created_at": g.created_at,
    }


def _get_own_generation(gen_id: int, user: User, db: Session) -> Generation:
    gen = db.get(Generation, gen_id)
    if gen is None or gen.user_id != user.id:
        raise HTTPException(status_code=404, detail="Generation not found")
    return gen


def _validate_generate_request(req: GenerateRequest) -> None:
    if not req.business_name.strip() or not req.description.strip():
        raise HTTPException(status_code=400, detail="Please fill in all fields")
    if req.style not in ai.STYLES:
        raise HTTPException(status_code=400, detail=f"Unknown style: {req.style}")
    ai.resolve_model(req.model)


def _check_daily_limit(user: User, db: Session) -> None:
    today_start = datetime.combine(datetime.now(timezone.utc).date(), time.min)
    used = (
        db.query(Generation)
        .filter(Generation.user_id == user.id, Generation.created_at >= today_start)
        .count()
    )
    limit = DAILY_LIMIT_DEMO if user.email == DEMO_EMAIL else DAILY_LIMIT
    if used >= limit:
        raise HTTPException(
            status_code=429,
            detail=f"Daily limit of {limit} generations reached. Try again tomorrow.",
        )


def _save_generation(req: GenerateRequest, html: str, user: User, db: Session) -> Generation:
    gen = Generation(
        user_id=user.id,
        business_name=req.business_name,
        description=req.description,
        answers=req.answers,
        style=req.style,
        language=req.language,
        model=req.model or ai.DEFAULT_MODEL_KEY,
        html=html,
    )
    db.add(gen)
    db.commit()
    return gen


@router.get("/models")
def list_models():
    return {"models": list(ai.MODELS.keys()), "default": ai.DEFAULT_MODEL_KEY}


@router.post("/clarify")
async def clarify(req: ClarifyRequest, user: User = Depends(get_current_user)):
    if not req.business_name.strip() or not req.description.strip():
        raise HTTPException(status_code=400, detail="Please fill in all fields")
    questions = await ai.clarify_questions(req.business_name, req.description, model_key=req.model)
    return {"questions": questions}


@router.post("/generate", status_code=201)
async def generate(
    req: GenerateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _validate_generate_request(req)
    _check_daily_limit(user, db)

    html = await ai.generate_landing(
        req.business_name, req.description, req.answers, req.style, req.language,
        model_key=req.model,
    )
    gen = _save_generation(req, html, user, db)
    return {**_summary(gen), "html": html}


@router.post("/generate/stream")
async def generate_stream(
    req: GenerateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _validate_generate_request(req)
    _check_daily_limit(user, db)

    prompt = ai.generate_prompt(
        req.business_name, req.description, req.answers, req.style, req.language
    )

    async def event_stream():
        def sse(payload: dict) -> str:
            return f"data: {json.dumps(payload)}\n\n"

        chunks: list[str] = []
        try:
            async for delta in ai.stream_groq(prompt, model_key=req.model):
                chunks.append(delta)
                yield sse({"delta": delta})

            html = ai.finalize_html("".join(chunks))
            if html is None:
                # streamed output came back incomplete — one silent non-stream retry
                text = await ai.call_groq(
                    prompt + ai.RETRY_SUFFIX, timeout=120.0,
                    max_tokens=ai.generation_max_tokens(req.model),
                    model_key=req.model,
                )
                html = ai.finalize_html(text)
            if html is None:
                yield sse({"error": "AI returned an incomplete page. Please try again."})
                return

            gen = _save_generation(req, html, user, db)
            yield sse({"done": True, "id": gen.id})
        except HTTPException as e:
            yield sse({"error": e.detail})
        except Exception:
            yield sse({"error": "Generation failed. Please try again."})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/generations")
def list_generations(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    gens = (
        db.query(Generation)
        .filter(Generation.user_id == user.id)
        .order_by(Generation.created_at.desc())
        .all()
    )
    return [_summary(g) for g in gens]


@router.get("/generations/{gen_id}")
def get_generation(
    gen_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    gen = _get_own_generation(gen_id, user, db)
    return {**_summary(gen), "html": gen.html}


@router.delete("/generations/{gen_id}", status_code=204)
def delete_generation(
    gen_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    gen = _get_own_generation(gen_id, user, db)
    db.delete(gen)
    db.commit()


@router.get("/generations/{gen_id}/download")
def download_generation(
    gen_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    gen = _get_own_generation(gen_id, user, db)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("index.html", gen.html)
    buf.seek(0)

    slug = re.sub(r"[^a-zA-Z0-9]+", "-", gen.business_name).strip("-").lower() or "landing"
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{slug}.zip"'},
    )
