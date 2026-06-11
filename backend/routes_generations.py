import io
import re
import zipfile

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from . import ai
from .auth import get_current_user
from .database import get_db
from .models import Generation, User

router = APIRouter(prefix="/api", tags=["generations"])


class ClarifyRequest(BaseModel):
    business_name: str
    description: str


class GenerateRequest(BaseModel):
    business_name: str
    description: str
    answers: str = ""
    style: str = "dark"
    language: str = "English"


def _summary(g: Generation) -> dict:
    return {
        "id": g.id,
        "business_name": g.business_name,
        "description": g.description,
        "style": g.style,
        "language": g.language,
        "created_at": g.created_at,
    }


def _get_own_generation(gen_id: int, user: User, db: Session) -> Generation:
    gen = db.get(Generation, gen_id)
    if gen is None or gen.user_id != user.id:
        raise HTTPException(status_code=404, detail="Generation not found")
    return gen


@router.post("/clarify")
async def clarify(req: ClarifyRequest, user: User = Depends(get_current_user)):
    if not req.business_name.strip() or not req.description.strip():
        raise HTTPException(status_code=400, detail="Please fill in all fields")
    questions = await ai.clarify_questions(req.business_name, req.description)
    return {"questions": questions}


@router.post("/generate", status_code=201)
async def generate(
    req: GenerateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not req.business_name.strip() or not req.description.strip():
        raise HTTPException(status_code=400, detail="Please fill in all fields")
    if req.style not in ai.STYLES:
        raise HTTPException(status_code=400, detail=f"Unknown style: {req.style}")

    html = await ai.generate_landing(
        req.business_name, req.description, req.answers, req.style, req.language
    )

    gen = Generation(
        user_id=user.id,
        business_name=req.business_name,
        description=req.description,
        answers=req.answers,
        style=req.style,
        language=req.language,
        html=html,
    )
    db.add(gen)
    db.commit()
    return {**_summary(gen), "html": html}


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
