import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

from .database import Base, engine
from . import auth, routes_generations

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Landing Studio")

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
