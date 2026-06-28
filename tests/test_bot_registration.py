"""Phase 3 + 4 tests: Telegram first-run registration and PDF-by-email.

Covers:
- the registration step machine advances one step per inbound message and
  completes (name → language → location → village → crops → farm size → email),
- a photo sent before completion nudges the farmer to finish registering,
- after completion a (monkeypatched) photo files a claim populated from the
  saved profile fields,
- the inline-button callback ``pdf:{id}`` with an email on file emails the PDF.

Everything that would touch the network (telegram_client send/download/document
and notifications.send_claim_pdf_email) is monkeypatched. The repo runs against
a throwaway sqlite file, mirroring tests/test_farmer_profiles.py.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest


@pytest.fixture()
def env(tmp_path, monkeypatch):
    """Point the engine at a throwaway sqlite file and reset the caches."""
    db_path = tmp_path / "registration_test.sqlite"
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
def tg(monkeypatch):
    """Stub the Telegram transport so nothing hits the network. Returns a
    MagicMock whose ``.sent`` list captures (chat_id, text) tuples."""
    from app.clients import telegram_client

    holder = MagicMock()
    holder.sent = []

    def _send_message(chat_id, text, *, reply_markup=None):
        holder.sent.append((chat_id, text))
        return {"ok": True}

    monkeypatch.setattr(telegram_client, "send_message", _send_message)
    monkeypatch.setattr(telegram_client, "send_document", MagicMock(return_value={"ok": True}))
    monkeypatch.setattr(
        telegram_client, "answer_callback_query", MagicMock(return_value={"ok": True})
    )
    return holder


def _step(chat_id: int, **kwargs):
    """Run one inbound message through the intake with sensible defaults."""
    from app.agents.whatsapp_intake import process_inbound_telegram

    payload = dict(
        chat_id=chat_id,
        user_name="Asha",
        body="",
        photo_file_id=None,
        mime=None,
        location=None,
        is_start=False,
    )
    payload.update(kwargs)
    return process_inbound_telegram(**payload)


# ─── registration step machine ──────────────────────────────────────────────


def test_full_registration_sequence_completes(env, tg):
    from app.storage import farmer_repo

    cid = 1001
    key = str(cid)

    # First contact → awaiting_name
    r = _step(cid, body="hi")
    assert r.status == "awaiting_name"
    assert farmer_repo.get_by_chat_id(key).registration_step == "awaiting_name"

    # Name → awaiting_language
    r = _step(cid, body="Asha Devi")
    assert r.status == "awaiting_language"
    prof = farmer_repo.get_by_chat_id(key)
    assert prof.name == "Asha Devi"
    assert prof.registration_step == "awaiting_language"

    # Language (typed) → awaiting_location
    r = _step(cid, body="हिन्दी")
    assert r.status == "awaiting_location"
    prof = farmer_repo.get_by_chat_id(key)
    assert prof.language == "hi"
    assert prof.registration_step == "awaiting_location"

    # Location share → awaiting_village
    r = _step(cid, location=(19.0, 73.0))
    assert r.status == "awaiting_village"
    prof = farmer_repo.get_by_chat_id(key)
    assert prof.latitude == 19.0 and prof.longitude == 73.0

    # Village → awaiting_crops (region back-filled from village)
    r = _step(cid, body="Wardha")
    assert r.status == "awaiting_crops"
    prof = farmer_repo.get_by_chat_id(key)
    assert prof.village == "Wardha"
    assert prof.region == "Wardha"

    # Crops → awaiting_farm_size
    r = _step(cid, body="cotton, soybean")
    assert r.status == "awaiting_farm_size"
    assert farmer_repo.get_by_chat_id(key).crops == "cotton, soybean"

    # Bad farm size re-asks
    r = _step(cid, body="quite big")
    assert r.status == "awaiting_farm_size"

    # Farm size ("2.5 ha") → awaiting_email
    r = _step(cid, body="2.5 ha")
    assert r.status == "awaiting_email"
    assert farmer_repo.get_by_chat_id(key).farm_area_hectares == 2.5

    # Email → complete
    r = _step(cid, body="asha@example.com")
    assert r.status == "registration_complete"
    prof = farmer_repo.get_by_chat_id(key)
    assert prof.email == "asha@example.com"
    assert prof.registration_step == "complete"
    assert prof.registration_complete is True


def test_language_callback_advances(env, tg):
    from app.agents.whatsapp_intake import process_telegram_callback
    from app.storage import farmer_repo

    cid = 1002
    _step(cid, body="hi")  # → awaiting_name
    _step(cid, body="Meera")  # → awaiting_language

    r = process_telegram_callback(
        chat_id=cid, user_name="Meera", data="lang:es", callback_query_id="cb1"
    )
    assert r.status == "awaiting_location"
    prof = farmer_repo.get_by_chat_id(str(cid))
    assert prof.language == "es"
    assert prof.registration_step == "awaiting_location"


def test_email_skip_leaves_email_empty(env, tg):
    from app.storage import farmer_repo

    cid = 1003
    key = str(cid)
    _step(cid, body="hi")
    _step(cid, body="Ravi")
    _step(cid, body="English")
    _step(cid, body="skip location")  # typed skip at location step
    _step(cid, body="Nagpur")
    _step(cid, body="rice")
    _step(cid, body="3")
    r = _step(cid, body="skip")
    assert r.status == "registration_complete"
    prof = farmer_repo.get_by_chat_id(key)
    assert prof.email == ""
    assert prof.registration_complete is True


# ─── photo before completion ────────────────────────────────────────────────


def test_photo_before_completion_nudges(env, tg, monkeypatch):
    """A photo sent mid-registration must NOT file a claim; it advances the
    current step (here: name) and the pipeline is never reached."""
    from app.agents.whatsapp_intake import process_inbound_telegram
    from app.clients import telegram_client

    download = MagicMock()
    monkeypatch.setattr(telegram_client, "download_file", download)

    cid = 1004
    _step(cid, body="hi")  # → awaiting_name

    r = process_inbound_telegram(
        chat_id=cid,
        user_name="Asha",
        body="my crop is dead",
        photo_file_id="file123",
        mime="image/jpeg",
    )
    # Still in registration — the caption was taken as the name, not a claim.
    assert r.status == "awaiting_language"
    download.assert_not_called()


# ─── claim after completion uses profile fields ─────────────────────────────


def _register(cid: int):
    """Drive a chat all the way to a complete profile."""
    _step(cid, body="hi")
    _step(cid, body="Asha Devi")
    _step(cid, body="हिन्दी")
    _step(cid, location=(19.5, 73.5))
    _step(cid, body="Wardha")
    _step(cid, body="cotton")
    _step(cid, body="4")
    _step(cid, body="asha@example.com")


def test_photo_after_completion_files_claim_from_profile(env, tg, monkeypatch):
    from app.agents import photo_forensics
    from app.agents.whatsapp_intake import process_inbound_telegram
    from app.clients import telegram_client
    from app.models.claim import Farmer

    cid = 1005
    _register(cid)

    # Stub the heavy pipeline. Capture the Farmer build_claim is handed.
    captured = {}

    img = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
    monkeypatch.setattr(telegram_client, "download_file", lambda fid: (img, "image/png"))
    monkeypatch.setattr(
        "app.agents.whatsapp_intake.assess_damage", lambda data_url: MagicMock()
    )
    monkeypatch.setattr(
        photo_forensics,
        "analyze",
        lambda b, u: MagicMock(gps_lat=None, gps_lon=None, capture_time=None),
    )
    monkeypatch.setattr(
        "app.agents.whatsapp_intake.corroborate",
        lambda damage, *, latitude, longitude, claim_date: (MagicMock(), MagicMock()),
    )

    def _build_claim(*, farmer: Farmer, **kwargs):
        captured["farmer"] = farmer
        claim = MagicMock()
        claim.claim_id = "CF-NEW-1"
        claim.photo_urls = []
        return claim

    monkeypatch.setattr("app.agents.whatsapp_intake.build_claim", _build_claim)
    monkeypatch.setattr(
        "app.agents.whatsapp_intake.render_claim_pdf", lambda claim, path: path
    )
    monkeypatch.setattr("app.storage.claims_repo.save", MagicMock())
    monkeypatch.setattr(
        "app.agents.whatsapp_intake.status_message",
        lambda claim, target_language=None: "ok",
    )
    # No prior photos for dedupe.
    monkeypatch.setattr("app.storage.claims_repo.list_by_status", lambda *a, **k: [])

    r = process_inbound_telegram(
        chat_id=cid,
        user_name="ignored-from-telegram",
        body="hailstorm flattened the field",
        photo_file_id="file999",
        mime="image/png",
    )

    assert r.status == "processed"
    assert r.claim_id == "CF-NEW-1"
    farmer = captured["farmer"]
    assert farmer.name == "Asha Devi"  # from profile, not the telegram first_name
    assert farmer.language == "hi"
    assert farmer.region == "Wardha"
    assert farmer.farm_area_hectares == 4.0
    assert farmer.latitude == 19.5 and farmer.longitude == 73.5
    assert farmer.phone == f"telegram:{cid}"


# ─── PDF-by-email callback ───────────────────────────────────────────────────


def test_pdf_callback_with_email_sends(env, tg, monkeypatch):
    from app.agents.whatsapp_intake import process_telegram_callback
    from app.clients import notifications
    from app.storage import claims_repo, farmer_repo

    cid = 1006
    key = str(cid)
    _register(cid)
    assert farmer_repo.get_by_chat_id(key).email == "asha@example.com"

    # A claim row with a pdf_path the helper can read.
    fake_row = MagicMock(pdf_path="/tmp/does-not-matter.pdf")
    monkeypatch.setattr(claims_repo, "get_row", lambda cidc: fake_row)
    monkeypatch.setattr(
        "app.agents.whatsapp_intake.Path",
        MagicMock(return_value=MagicMock(read_bytes=lambda: b"%PDF-1.4 fake")),
    )

    send_mock = MagicMock(return_value=MagicMock(delivered=True))
    monkeypatch.setattr(notifications, "send_claim_pdf_email", send_mock)

    r = process_telegram_callback(
        chat_id=cid, user_name="Asha", data="pdf:CF-XYZ", callback_query_id="cb9"
    )

    assert r.status == "pdf_emailed"
    send_mock.assert_called_once()
    _, kwargs = send_mock.call_args
    assert kwargs["to"] == "asha@example.com"
    assert kwargs["claim_id"] == "CF-XYZ"
    assert kwargs["farmer_name"] == "Asha Devi"


def test_pdf_callback_without_email_sets_pending_then_collects(env, tg, monkeypatch):
    from app.agents.whatsapp_intake import process_telegram_callback
    from app.clients import notifications
    from app.storage import claims_repo, farmer_repo

    cid = 1007
    key = str(cid)
    # Register but skip the email.
    _step(cid, body="hi")
    _step(cid, body="Ravi")
    _step(cid, body="English")
    _step(cid, body="skip")
    _step(cid, body="Pune")
    _step(cid, body="wheat")
    _step(cid, body="2")
    _step(cid, body="skip")
    assert farmer_repo.get_by_chat_id(key).email == ""

    # Tap "email me a PDF" with no email on file → pending state set.
    r = process_telegram_callback(
        chat_id=cid, user_name="Ravi", data="pdf:CF-ABC", callback_query_id="cb1"
    )
    assert r.status == "awaiting_pdf_email"
    assert farmer_repo.get_by_chat_id(key).pending_pdf_claim_id == "CF-ABC"

    # Now an email message completes the send and clears the pending flag.
    fake_row = MagicMock(pdf_path="/tmp/x.pdf")
    monkeypatch.setattr(claims_repo, "get_row", lambda c: fake_row)
    monkeypatch.setattr(
        "app.agents.whatsapp_intake.Path",
        MagicMock(return_value=MagicMock(read_bytes=lambda: b"%PDF")),
    )
    send_mock = MagicMock(return_value=MagicMock(delivered=True))
    monkeypatch.setattr(notifications, "send_claim_pdf_email", send_mock)

    r = _step(cid, body="ravi@example.com")
    assert r.status == "pdf_emailed"
    send_mock.assert_called_once()
    prof = farmer_repo.get_by_chat_id(key)
    assert prof.email == "ravi@example.com"
    assert prof.pending_pdf_claim_id is None
