"""SEC-007 regression: with AUTH_DEV_LINKS off (the secure default) the auth
endpoints must NOT echo live verification/reset/magic-link tokens in their
JSON responses. Returning a reset link for a registered email would be an
account-takeover vector in production.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "sec007.sqlite"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("PUBLIC_BASE_URL", "http://testserver")
    # Explicitly secure config: dev links OFF, no email transport.
    monkeypatch.setenv("AUTH_DEV_LINKS", "false")
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    monkeypatch.delenv("SENDGRID_API_KEY", raising=False)

    from app import config
    from app.storage import db as db_module

    config.get_settings.cache_clear()
    db_module.get_engine.cache_clear()

    from app.main import app

    with TestClient(app) as c:
        yield c

    db_module.get_engine.cache_clear()
    config.get_settings.cache_clear()


def _sign_up(client: TestClient, email: str) -> dict:
    r = client.post(
        "/auth/sign-up",
        json={"email": email, "password": "hunter22A!", "name": "QA"},
    )
    assert r.status_code == 201, r.text
    return r.json()


def test_signup_does_not_leak_verification_url(client: TestClient) -> None:
    body = _sign_up(client, "sec007-signup@claimfarm.dev")
    assert "verification_url" not in body
    assert body.get("verification_email_sent") is False


def test_reset_does_not_leak_reset_url(client: TestClient) -> None:
    email = "sec007-reset@claimfarm.dev"
    _sign_up(client, email)
    # Reset for a REGISTERED email must still 200 (no enumeration) but must
    # NOT return a usable reset link.
    r = client.post("/auth/reset", json={"email": email})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body == {"ok": True}
    assert "reset_url" not in body


def test_magic_link_does_not_leak_consume_url(client: TestClient) -> None:
    email = "sec007-magic@claimfarm.dev"
    _sign_up(client, email)
    r = client.post("/auth/magic-link", json={"email": email})
    assert r.status_code == 200, r.text
    body = r.json()
    assert "consume_url" not in body
