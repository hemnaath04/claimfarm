"""Phase 2 farmer-profile tests.

Covers the SQLite repo round-trip (upsert / get_by_chat_id / update /
list_all) and the admin-gated GET /api/farmers endpoint (anon -> 401,
authed -> 200 with items).
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def env(tmp_path, monkeypatch):
    """Point the engine at a throwaway sqlite file and reset the caches."""
    db_path = tmp_path / "farmers_test.sqlite"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("PUBLIC_BASE_URL", "http://testserver")
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    monkeypatch.delenv("SENDGRID_API_KEY", raising=False)

    from app import config
    from app.storage import db as db_module

    config.get_settings.cache_clear()
    db_module.get_engine.cache_clear()

    yield

    db_module.get_engine.cache_clear()
    config.get_settings.cache_clear()


@pytest.fixture()
def client(env):
    from app.main import app

    # The lead wires app/api_farmers into main.py at integration time; mount
    # it here so the endpoint is reachable under test in isolation. Guard
    # against a double-include once the wiring lands.
    from app.api_farmers import router as farmers_router

    if not any(getattr(r, "path", None) == "/api/farmers" for r in app.routes):
        app.include_router(farmers_router)

    with TestClient(app) as c:
        yield c


def _sign_up(client: TestClient, email: str, password: str = "Hunter22A!") -> dict:
    r = client.post(
        "/auth/sign-up",
        json={"email": email, "password": password, "name": "Test"},
    )
    assert r.status_code == 201, r.text
    return r.json()


def _session_for(client: TestClient, email: str, password: str = "Hunter22A!") -> TestClient:
    client.cookies.clear()
    r = client.post("/auth/sign-in", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return client


# ---------- repo round-trip ----------


def test_repo_upsert_and_get(env):
    from app.storage import farmer_repo
    from app.storage.farmer_repo import FarmerProfileRow

    row = FarmerProfileRow(chat_id="42", name="Asha", language="hi", phone="telegram:42")
    saved = farmer_repo.upsert(row)
    assert saved.farmer_id.startswith("frm_")

    got = farmer_repo.get_by_chat_id("42")
    assert got is not None
    assert got.name == "Asha"
    assert got.language == "hi"

    assert farmer_repo.get_by_chat_id("does-not-exist") is None


def test_repo_upsert_is_idempotent_by_chat_id(env):
    from app.storage import farmer_repo
    from app.storage.farmer_repo import FarmerProfileRow

    first = farmer_repo.upsert(FarmerProfileRow(chat_id="7", name="One"))
    second = farmer_repo.upsert(FarmerProfileRow(chat_id="7", name="Two"))

    # Same chat_id -> single row, updated in place (farmer_id preserved).
    assert second.farmer_id == first.farmer_id
    assert second.name == "Two"
    assert len(farmer_repo.list_all()) == 1


def test_repo_update_and_completion_flag(env):
    from app.storage import farmer_repo
    from app.storage.farmer_repo import FarmerProfileRow

    farmer_repo.upsert(FarmerProfileRow(chat_id="9", name="Initial"))

    updated = farmer_repo.update("9", name="Renamed", village="Greenfield")
    assert updated is not None
    assert updated.name == "Renamed"
    assert updated.village == "Greenfield"
    assert updated.registration_complete is False

    done = farmer_repo.update("9", registration_step="complete")
    assert done is not None
    assert done.registration_complete is True

    assert farmer_repo.update("missing", name="x") is None


def test_repo_get_or_create(env):
    from app.storage import farmer_repo

    created = farmer_repo.get_or_create("100", name="Fresh", phone="telegram:100")
    assert created.name == "Fresh"

    again = farmer_repo.get_or_create("100", name="Ignored")
    assert again.farmer_id == created.farmer_id
    assert again.name == "Fresh"  # defaults ignored when the row exists


def test_repo_list_all_newest_first(env):
    import time

    from app.storage import farmer_repo
    from app.storage.farmer_repo import FarmerProfileRow

    farmer_repo.upsert(FarmerProfileRow(chat_id="a", name="First"))
    time.sleep(0.01)
    farmer_repo.upsert(FarmerProfileRow(chat_id="b", name="Second"))

    rows = farmer_repo.list_all()
    assert [r.name for r in rows] == ["Second", "First"]


# ---------- API ----------


def test_farmers_requires_auth(client: TestClient):
    client.cookies.clear()
    r = client.get("/api/farmers")
    assert r.status_code == 401


def test_farmers_authed_returns_items(client: TestClient):
    from app.storage import farmer_repo
    from app.storage.farmer_repo import FarmerProfileRow

    farmer_repo.upsert(
        FarmerProfileRow(
            chat_id="555",
            name="Meera",
            language="hi",
            region="Maharashtra",
            village="Wardha",
            crops="cotton,soybean",
            farm_area_hectares=3.5,
            email="meera@example.com",
            phone="telegram:555",
            registration_step="complete",
            registration_complete=True,
        )
    )

    _sign_up(client, "adjuster@example.com")
    _session_for(client, "adjuster@example.com")

    r = client.get("/api/farmers")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["total"] == 1
    item = body["items"][0]
    assert item["name"] == "Meera"
    assert item["crops"] == "cotton,soybean"
    assert item["registration_complete"] is True
    assert item["claim_count"] == 0
    assert "created_at" in item
