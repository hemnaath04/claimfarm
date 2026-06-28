"""Phase 5 invite-only access.

Covers:
- Owner can mint an invite; non-owner roles get 403.
- Accepting a valid token creates a user with the invite's role and marks the
  invite used; reusing the token is rejected (400).
- Open sign-up is closed (403) once any user exists, but the very first sign-up
  bootstraps the owner account.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "invites.sqlite"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("PUBLIC_BASE_URL", "http://testserver")
    monkeypatch.setenv("AUTH_DEV_LINKS", "false")
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    monkeypatch.delenv("SENDGRID_API_KEY", raising=False)

    from app import config
    from app.storage import db as db_module

    config.get_settings.cache_clear()
    db_module.get_engine.cache_clear()

    from app.main import app
    from app.middlewares import IPRateLimiter

    # The lead wires app.api_invites.router into main.py for the integration
    # build; mount it here too so this suite is self-contained regardless of
    # wiring order. Idempotent: skip if already registered.
    from app.api_invites import router as invites_router

    if not any(getattr(r, "path", "") == "/api/admin/invites" for r in app.routes):
        app.include_router(invites_router)
        app.middleware_stack = app.build_middleware_stack()

    # Reset the shared per-IP rate-limit bucket between tests (see RBAC suite).
    asgi = app.middleware_stack
    while asgi is not None:
        if isinstance(asgi, IPRateLimiter):
            asgi._hits.clear()
            break
        asgi = getattr(asgi, "app", None)

    with TestClient(app) as c:
        yield c

    db_module.get_engine.cache_clear()
    config.get_settings.cache_clear()


def _sign_up(client: TestClient, email: str, password: str = "Hunter22A!") -> dict:
    r = client.post(
        "/auth/sign-up",
        json={"email": email, "password": password, "name": "Test"},
    )
    assert r.status_code == 201, r.text
    return r.json()


def _force_role(user_id: str, role: str) -> None:
    from app.storage import users_repo

    row = users_repo.get(user_id)
    assert row is not None
    row.role = role
    users_repo.upsert(row)


def _session_for(client: TestClient, email: str, password: str = "Hunter22A!") -> None:
    client.cookies.clear()
    r = client.post("/auth/sign-in", json={"email": email, "password": password})
    assert r.status_code == 200, r.text


def _owner_client(client: TestClient) -> dict:
    """First sign-up bootstraps the owner; return its session-backed client."""
    data = _sign_up(client, "owner@example.com")
    _session_for(client, "owner@example.com")
    return data


# ---------- issuance ----------

def test_owner_can_create_invite(client):
    _owner_client(client)
    r = client.post("/api/admin/invites", json={"email": "new@example.com", "role": "reviewer"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["invite"]["role"] == "reviewer"
    assert body["invite"]["used"] is False
    assert body["accept_url"].endswith(f"invite={_token_from_url(body['accept_url'])}")


def test_non_owner_cannot_create_invite(client):
    # Bootstrap owner first, then create a second user demoted to admin.
    _owner_client(client)
    actor = _sign_up_via_invite(client, role="admin")
    _session_for(client, actor["email"])
    r = client.post("/api/admin/invites", json={"role": "reviewer"})
    assert r.status_code == 403, r.text


def test_create_invite_rejects_owner_role(client):
    _owner_client(client)
    r = client.post("/api/admin/invites", json={"role": "owner"})
    assert r.status_code == 400, r.text


# ---------- acceptance ----------

def test_accept_invite_creates_user_and_consumes_token(client):
    _owner_client(client)
    r = client.post("/api/admin/invites", json={"email": "invitee@example.com", "role": "moderator"})
    token = _token_from_url(r.json()["accept_url"])

    client.cookies.clear()
    accept = client.post(
        "/auth/accept-invite",
        json={"token": token, "password": "Sup3rSecret!", "name": "Invitee"},
    )
    assert accept.status_code == 201, accept.text
    assert accept.json()["role"] == "moderator"

    from app.storage import users_repo

    created = users_repo.get_by_email("invitee@example.com")
    assert created is not None
    assert created.role == "moderator"
    assert created.email_verified is True

    # Reusing the same token must now fail.
    reuse = client.post(
        "/auth/accept-invite",
        json={"token": token, "password": "Another1!", "name": "Dup"},
    )
    assert reuse.status_code == 400, reuse.text


def test_accept_invite_bad_token(client):
    _owner_client(client)
    client.cookies.clear()
    r = client.post(
        "/auth/accept-invite",
        json={"token": "nope-not-real", "password": "Sup3rSecret!"},
    )
    assert r.status_code == 400, r.text


# ---------- sign-up gating ----------

def test_signup_blocked_once_a_user_exists(client):
    _sign_up(client, "first@example.com")  # bootstrap owner
    r = client.post(
        "/auth/sign-up",
        json={"email": "second@example.com", "password": "Hunter22A!", "name": "No"},
    )
    assert r.status_code == 403, r.text


def test_bootstrap_signup_creates_owner(client):
    data = _sign_up(client, "boss@example.com")
    from app.storage import users_repo

    row = users_repo.get(data["user_id"])
    assert row is not None
    assert row.role == "owner"


# ---------- helpers ----------

def _token_from_url(url: str) -> str:
    return url.split("invite=", 1)[1]


def _sign_up_via_invite(client: TestClient, role: str) -> dict:
    """Owner mints an invite for `role`; an invitee accepts it. Returns the
    new user's dict augmented with its email/password for re-auth."""
    r = client.post("/api/admin/invites", json={"email": f"{role}@example.com", "role": role})
    assert r.status_code == 200, r.text
    token = _token_from_url(r.json()["accept_url"])
    client.cookies.clear()
    accept = client.post(
        "/auth/accept-invite",
        json={"token": token, "password": "Hunter22A!", "name": role},
    )
    assert accept.status_code == 201, accept.text
    out = accept.json()
    out["email"] = f"{role}@example.com"
    return out
