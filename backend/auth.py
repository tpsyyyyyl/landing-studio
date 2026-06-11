import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from .database import get_db
from .models import User

router = APIRouter(prefix="/api/auth", tags=["auth"])

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-in-production-0000")
JWT_ALGORITHM = "HS256"
TOKEN_TTL_DAYS = 7

DEMO_EMAIL = "demo@landing.studio"
DEMO_PASSWORD = "demo1234"

security = HTTPBearer()


class Credentials(BaseModel):
    email: EmailStr
    password: str


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(days=TOKEN_TTL_DAYS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = db.get(User, int(payload["sub"]))
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@router.post("/register", status_code=201)
def register(creds: Credentials, db: Session = Depends(get_db)):
    if len(creds.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    if db.query(User).filter(User.email == creds.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(email=creds.email, password_hash=hash_password(creds.password))
    db.add(user)
    db.commit()
    return {"token": create_token(user.id), "email": user.email}


@router.post("/login")
def login(creds: Credentials, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == creds.email).first()
    if user is None or not verify_password(creds.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return {"token": create_token(user.id), "email": user.email}


@router.post("/demo")
def demo_login(db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == DEMO_EMAIL).first()
    if user is None:
        raise HTTPException(status_code=503, detail="Demo account is not set up")
    return {"token": create_token(user.id), "email": user.email}


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {"id": user.id, "email": user.email, "created_at": user.created_at}
