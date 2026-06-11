import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

_default_sqlite = os.getenv(
    "DATABASE_PATH",
    os.path.join(os.path.dirname(__file__), "..", "landing_studio.db"),
)

# Full SQLAlchemy URL (e.g. postgresql+psycopg://... on Render); defaults to local SQLite
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{_default_sqlite}")
if DATABASE_URL.startswith("postgres://"):
    # Render emits postgres:// which SQLAlchemy 2 no longer accepts
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)

_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
