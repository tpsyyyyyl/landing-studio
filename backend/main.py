import logging
import os
import time

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

from . import ai, auth, routes_generations
from .database import Base, SessionLocal, engine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("landing_studio")

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Landing Studio")


@app.middleware("http")
async def log_requests(request, call_next):
    started = time.monotonic()
    response = await call_next(request)
    if request.url.path.startswith("/api"):
        logger.info(
            "%s %s -> %d (%.0fms)",
            request.method,
            request.url.path,
            response.status_code,
            (time.monotonic() - started) * 1000,
        )
    return response


@app.get("/api/health")
def health():
    db_ok = True
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
    except Exception:
        db_ok = False
    return {"status": "ok" if db_ok else "degraded", "db": db_ok, "model": ai.DEFAULT_MODEL_KEY}


app.include_router(auth.router)
app.include_router(routes_generations.router)

_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(_dist, "assets")), name="assets")

    # SPA fallback: client-side routes (/dashboard, /preview/3) must serve index.html
    @app.get("/{path:path}")
    def spa(path: str):
        file = os.path.join(_dist, path)
        if path and os.path.isfile(file):
            return FileResponse(file)
        return FileResponse(os.path.join(_dist, "index.html"))
