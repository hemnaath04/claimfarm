"""HTTP-level coverage for the new auth/account endpoints.

Specifically locks in:
- POST /api/keys returns plaintext secret exactly once and is serializable
  after the session closes (regression against a SQLModel detached-instance
  500 that bit on first deploy).
- GET  /api/keys lists what was just issued; DELETE revokes it.
- GET  /api/me/export streams a downloadable JSON bundle whose shape is the
  public GDPR contract — schema_version + user + claims + audit_log keys.
- POST /api/me/delete soft-deletes the user; subsequent /auth/me is 401.
- POST /auth/magic-link always returns 200 regardless of email existence
  (no enumeration), and a valid token round-trips through /consume.
"""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "test.sqlite"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    # Force a fresh engine + settings for this test module.
    from app import config
    from app.storage import db as db_module

    config.get_settings.cache_clear()
    db_module.get_engine.cache_clear()

    from app.main import app  # imported after env override

    with TestClient(app) as c:
        yield c

    db_module.get_engine.cache_clear()
    config.get_settings.cache_clear()


def _sign_up(client: TestClient, email: str = "qa@claimfarm.dev") -> TestClient:
    r = client.post(
        "/auth/sign-up",
        json={"email": email, "password": "hunter22A!", "name": "QA User"},
    )
    assert r.status_code == 201, r.text
    return client


def test_api_keys_issue_list_revoke_round_trip(client: TestClient) -> None:
    _sign_up(client)

    issued = client.post("/api/keys", json={"name": "ci", "scope": "claims:read"})
    assert issued.status_code == 201, issued.text
    body = issued.json()
    assert body["scope"] == "claims:read"
    assert body["secret"].startswith("cf_live_")
    assert len(body["secret"]) > 32, "secret looks too short to be high-entropy"
    key_id = body["key_id"]

    listed = client.get("/api/keys").json()
    assert any(item["key_id"] == key_id for item in listed["items"])
    # Listing must never leak the plaintext secret a second time.
    assert all("secret" not in item for item in listed["items"])

    revoked = client.delete(f"/api/keys/{key_id}")
    assert revoked.status_code == 200

    after = client.get("/api/keys").json()
    revoked_row = next(i for i in after["items"] if i["key_id"] == key_id)
    assert revoked_row["revoked_at"] is not None


def test_gdpr_export_bundle_shape(client: TestClient) -> None:
    _sign_up(client, email="export@claimfarm.dev")
    r = client.get("/api/me/export")
    assert r.status_code == 200
    assert "attachment" in r.headers.get("content-disposition", "").lower()
    bundle = json.loads(r.content)
    # Contract for downstream tools / regulators.
    assert bundle["schema_version"] == 1
    for key in ("exported_at", "user", "claims", "audit_log"):
        assert key in bundle, f"missing {key} in export"
    assert bundle["user"]["email"] == "export@claimfarm.dev"


def test_account_soft_delete_revokes_session(client: TestClient) -> None:
    _sign_up(client, email="delete-me@claimfarm.dev")
    assert client.get("/auth/me").status_code == 200

    r = client.post("/api/me/delete")
    assert r.status_code == 200
    body = r.json()
    assert body["soft_deleted"] is True
    assert body["hard_delete_scheduled_for"].endswith("Z")

    # Session cookie must no longer authenticate.
    assert client.get("/auth/me").status_code == 401


def test_magic_link_request_never_enumerates(client: TestClient) -> None:
    # Unknown email still returns 200 — must not reveal account existence.
    r = client.post("/auth/magic-link", json={"email": "nobody@example.com"})
    assert r.status_code == 200
    assert r.json() == {"ok": True}

    _sign_up(client, email="ml@claimfarm.dev")
    r2 = client.post("/auth/magic-link", json={"email": "ml@claimfarm.dev"})
    assert r2.status_code == 200


def test_magic_link_consume_signs_in(client: TestClient) -> None:
    _sign_up(client, email="ml-consume@claimfarm.dev")
    # Drop the session cookie so consume gets a fresh one.
    client.cookies.clear()

    # Mint a token the same way the email path would, without touching SMTP.
    from app.api_magic_link import _issue_magic_link_token
    from app.storage import users_repo

    user = users_repo.get_by_email("ml-consume@claimfarm.dev")
    assert user is not None
    token = _issue_magic_link_token(user.user_id)

    consumed = client.get(f"/auth/magic-link/consume?token={token}&redirect=false")
    assert consumed.status_code == 200, consumed.text
    assert consumed.json()["user_id"] == user.user_id

    # Fresh session cookie should now authenticate /auth/me.
    me = client.get("/auth/me")
    assert me.status_code == 200, me.text

    # Single-use: the same token must not redeem again.
    again = client.get(f"/auth/magic-link/consume?token={token}&redirect=false")
    assert again.status_code == 400
