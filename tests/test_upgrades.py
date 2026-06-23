import os
import tempfile

os.environ["DATABASE_PATH"] = os.path.join(tempfile.mkdtemp(), "test.db")
os.environ.setdefault("GROQ_API_KEY", "test-key")

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from backend import ai, routes_generations
from backend.ai import finalize_html
from backend.main import app

client = TestClient(app)

COMPLETE_HTML = "<!DOCTYPE html>\n<html><body>" + "x" * 2100 + "</body></html>"
NO_DOCTYPE_HTML = "<html><body>" + "x" * 2100 + "</body></html>"
TRUNCATED_HTML = "<!DOCTYPE html>\n<html><body>" + "x" * 2100 + "<div>cut off"


def auth_header():
    r = client.post("/api/auth/register", json={"email": "up@b.com", "password": "password1"})
    if r.status_code == 409:
        r = client.post("/api/auth/login", json={"email": "up@b.com", "password": "password1"})
    return {"Authorization": f"Bearer {r.json()['token']}"}


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["db"] is True
    assert body["model"] in ai.MODELS


def test_models_endpoint():
    r = client.get("/api/models")
    assert r.status_code == 200
    assert set(r.json()["models"]) == {"scout", "gpt-oss"}


FAILSAFE_MARKER = "section.reveal:not(.visible)"


def _assert_finalized(result, source_html):
    """Result preserves source content and has failsafe injected before </html>."""
    assert result is not None
    assert result.endswith("</html>")
    assert source_html.removesuffix("</html>") in result
    assert FAILSAFE_MARKER in result


def test_finalize_html():
    _assert_finalized(finalize_html(COMPLETE_HTML), COMPLETE_HTML)
    assert finalize_html(NO_DOCTYPE_HTML).startswith("<!DOCTYPE html>")
    assert finalize_html(TRUNCATED_HTML) is None
    assert finalize_html("<html></html>") is None  # too short
    _assert_finalized(finalize_html("```html\n" + COMPLETE_HTML + "\n```"), COMPLETE_HTML)


@pytest.mark.anyio
async def test_generate_retries_on_truncated_output(monkeypatch):
    calls = []

    async def fake_call_groq(prompt, timeout, max_tokens=4096, model_key=""):
        calls.append(prompt)
        return TRUNCATED_HTML if len(calls) == 1 else COMPLETE_HTML

    monkeypatch.setattr(ai, "call_groq", fake_call_groq)
    html = await ai.generate_landing("X", "Y", "", "dark", "English")
    _assert_finalized(html, COMPLETE_HTML)
    assert len(calls) == 2
    assert "COMPLETE HTML document" in calls[1]


@pytest.mark.anyio
async def test_generate_fails_after_two_truncated(monkeypatch):
    async def fake_call_groq(prompt, timeout, max_tokens=4096, model_key=""):
        return TRUNCATED_HTML

    monkeypatch.setattr(ai, "call_groq", fake_call_groq)
    with pytest.raises(HTTPException) as exc:
        await ai.generate_landing("X", "Y", "", "dark", "English")
    assert exc.value.status_code == 502


def test_unknown_model_rejected():
    r = client.post(
        "/api/generate",
        json={"business_name": "A", "description": "B", "model": "gpt5"},
        headers=auth_header(),
    )
    assert r.status_code == 400


def test_daily_rate_limit(monkeypatch):
    async def fake_generate(*args, **kwargs):
        return COMPLETE_HTML

    monkeypatch.setattr(ai, "generate_landing", fake_generate)
    monkeypatch.setattr(routes_generations, "DAILY_LIMIT", 2)

    headers = auth_header()
    body = {"business_name": "Limit", "description": "Test"}
    # fresh user may already have generations from other tests in this module — none here
    assert client.post("/api/generate", json=body, headers=headers).status_code == 201
    assert client.post("/api/generate", json=body, headers=headers).status_code == 201
    r = client.post("/api/generate", json=body, headers=headers)
    assert r.status_code == 429
    assert "Daily limit" in r.json()["detail"]


def test_stream_endpoint(monkeypatch):
    async def fake_stream(prompt, max_tokens=8192, model_key=""):
        half = len(COMPLETE_HTML) // 2
        yield COMPLETE_HTML[:half]
        yield COMPLETE_HTML[half:]

    monkeypatch.setattr(ai, "stream_groq", fake_stream)

    with client.stream(
        "POST",
        "/api/generate/stream",
        json={"business_name": "Stream", "description": "Test"},
        headers=auth_header(),
    ) as r:
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("text/event-stream")
        events = [l for l in r.iter_lines() if l.startswith("data: ")]

    import json as _json

    payloads = [_json.loads(e[6:]) for e in events]
    assert any(p.get("delta") for p in payloads)
    final = payloads[-1]
    assert final.get("done") is True and isinstance(final.get("id"), int)
