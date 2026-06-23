import io
import os
import tempfile
import zipfile

os.environ["DATABASE_PATH"] = os.path.join(tempfile.mkdtemp(), "test.db")
os.environ.setdefault("GROQ_API_KEY", "test-key")

import pytest
from fastapi.testclient import TestClient

from backend import ai
from backend.main import app

client = TestClient(app)

FAKE_HTML = "<!DOCTYPE html><html><body><h1>Fake</h1></body></html>"


@pytest.fixture(autouse=True)
def mock_ai(monkeypatch):
    async def fake_clarify(business_name, description, model_key=""):
        return ["Q1?", "Q2?", "Q3?", "Q4?", "Q5?"]

    async def fake_generate(business_name, description, answers, style, language, model_key=""):
        return FAKE_HTML

    monkeypatch.setattr(ai, "clarify_questions", fake_clarify)
    monkeypatch.setattr(ai, "generate_landing", fake_generate)


@pytest.fixture
def token():
    r = client.post("/api/auth/register", json={"email": "gen@b.com", "password": "password1"})
    if r.status_code == 409:
        r = client.post("/api/auth/login", json={"email": "gen@b.com", "password": "password1"})
    return r.json()["token"]


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_clarify(token):
    r = client.post(
        "/api/clarify",
        json={"business_name": "Cafe", "description": "Coffee shop"},
        headers=auth(token),
    )
    assert r.status_code == 200
    assert len(r.json()["questions"]) == 5


def test_generate_persists_and_full_crud(token):
    r = client.post(
        "/api/generate",
        json={
            "business_name": "Cafe",
            "description": "Coffee shop",
            "answers": "young people",
            "style": "light",
            "language": "English",
        },
        headers=auth(token),
    )
    assert r.status_code == 201
    gen_id = r.json()["id"]
    assert r.json()["html"] == FAKE_HTML

    r = client.get("/api/generations", headers=auth(token))
    assert r.status_code == 200
    items = r.json()
    assert any(g["id"] == gen_id for g in items)
    assert "html" not in items[0]

    r = client.get(f"/api/generations/{gen_id}", headers=auth(token))
    assert r.status_code == 200
    assert r.json()["html"] == FAKE_HTML

    r = client.get(f"/api/generations/{gen_id}/download", headers=auth(token))
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/zip"
    zf = zipfile.ZipFile(io.BytesIO(r.content))
    assert zf.read("index.html").decode() == FAKE_HTML

    r = client.delete(f"/api/generations/{gen_id}", headers=auth(token))
    assert r.status_code == 204
    r = client.get(f"/api/generations/{gen_id}", headers=auth(token))
    assert r.status_code == 404


def test_generate_unknown_style(token):
    r = client.post(
        "/api/generate",
        json={"business_name": "X", "description": "Y", "style": "neon"},
        headers=auth(token),
    )
    assert r.status_code == 400


def test_generations_isolated_between_users(token):
    r = client.post(
        "/api/generate",
        json={"business_name": "Mine", "description": "Secret"},
        headers=auth(token),
    )
    gen_id = r.json()["id"]

    r2 = client.post("/api/auth/register", json={"email": "other@b.com", "password": "password1"})
    other = r2.json()["token"]
    r = client.get(f"/api/generations/{gen_id}", headers=auth(other))
    assert r.status_code == 404


def test_endpoints_require_auth():
    assert client.post("/api/clarify", json={"business_name": "a", "description": "b"}).status_code == 401
    assert client.get("/api/generations").status_code == 401


def test_finalize_html_injects_failsafe():
    # Валідний мінімальний HTML > 2000 символів з section.reveal
    body = "<section class=\"reveal\">content</section>" + ("x" * 2000)
    html_input = f"<!doctype html><html><head></head><body>{body}</body></html>"
    result = ai.finalize_html(html_input)
    assert result is not None
    assert "<noscript>" in result
    assert "reveal:not(.visible)" in result
    assert result.rfind("<noscript>") < result.rfind("</html>")


def test_finalize_html_invalid_returns_none():
    result = ai.finalize_html("just some text without closing html tag")
    assert result is None
