import os
import tempfile

os.environ["DATABASE_PATH"] = os.path.join(tempfile.mkdtemp(), "test.db")
os.environ.setdefault("GROQ_API_KEY", "test-key")

from fastapi.testclient import TestClient

from backend.main import app
from backend.auth import DEMO_EMAIL, hash_password
from backend.database import SessionLocal
from backend.models import User

client = TestClient(app)


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_register_and_me():
    r = client.post("/api/auth/register", json={"email": "a@b.com", "password": "password1"})
    assert r.status_code == 201
    token = r.json()["token"]

    r = client.get("/api/auth/me", headers=auth_header(token))
    assert r.status_code == 200
    assert r.json()["email"] == "a@b.com"


def test_register_duplicate_email():
    client.post("/api/auth/register", json={"email": "dup@b.com", "password": "password1"})
    r = client.post("/api/auth/register", json={"email": "dup@b.com", "password": "password1"})
    assert r.status_code == 409


def test_register_short_password():
    r = client.post("/api/auth/register", json={"email": "short@b.com", "password": "1234"})
    assert r.status_code == 400


def test_login_ok_and_wrong_password():
    client.post("/api/auth/register", json={"email": "login@b.com", "password": "password1"})

    r = client.post("/api/auth/login", json={"email": "login@b.com", "password": "password1"})
    assert r.status_code == 200
    assert "token" in r.json()

    r = client.post("/api/auth/login", json={"email": "login@b.com", "password": "wrongpass"})
    assert r.status_code == 401


def test_me_without_token():
    r = client.get("/api/auth/me")
    assert r.status_code == 401


def test_me_with_garbage_token():
    r = client.get("/api/auth/me", headers=auth_header("garbage"))
    assert r.status_code == 401


def test_demo_login():
    r = client.post("/api/auth/demo")
    assert r.status_code == 503  # seed not run yet

    db = SessionLocal()
    db.add(User(email=DEMO_EMAIL, password_hash=hash_password("demo1234")))
    db.commit()
    db.close()

    r = client.post("/api/auth/demo")
    assert r.status_code == 200
    assert r.json()["email"] == DEMO_EMAIL
