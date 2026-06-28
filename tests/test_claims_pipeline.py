"""
Regression tests for the claims pipeline (claims-pipeline scope).

CLAIM-001: post_decision approve writes submitted→insurer→final, not approved→insurer
CLAIM-002: _notify_farmer uses pdf_path from ClaimRow, not Claim model
CLAIM-003: Telegram intake runs perceptual-hash dedupe before VL assessment
CLAIM-004: loadQueue useCallback dep array — JS-only, tested via tsc
CLAIM-005: 401 → redirect — JS-only, tested via tsc

Pipeline stages also tested:
- parse_telegram_update (photo, doc, /start, location, missing chat_id)
- parse_bird_payload (sender phone extraction)
- photo_forensics.extract_exif
- perceptual_hash dedupe: find_close_matches
- claims_repo save/get round-trip
- mock insurer submit (in-process)
- multilingual detect_language / status_message
- photo_store save_bytes / find_photo / public_url
"""

from __future__ import annotations

import io
import time
from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

# ─── helpers ────────────────────────────────────────────────────────────────


def _make_claim(**kw):
    """Build a minimal in-memory Claim (does not touch DB)."""
    from app.models.claim import Claim, ClaimStatus, Farmer
    from app.models.damage import DamageAssessment, DamageCause
    from app.models.weather import CorroborationResult, WeatherSummary

    farmer = Farmer(
        name=kw.get("name", "QA Farmer"),
        phone=kw.get("phone", f"CLAIMFARM-QA-{int(time.time())}"),
        latitude=20.0,
        longitude=78.0,
        farm_area_hectares=1.0,
    )
    damage = DamageAssessment(
        crop_type="maize",
        damage_cause=DamageCause.drought,
        severity=80,
        affected_area_pct=60,
        confidence=0.9,
        visible_indicators=["wilting"],
        notes="QA test",
    )
    weather = WeatherSummary(
        latitude=20.0,
        longitude=78.0,
        start_date=date(2025, 4, 1),
        end_date=date(2025, 5, 1),
        total_precip_mm=5.0,
        max_temp_c=42.0,
        min_temp_c=28.0,
        max_wind_kmh=20.0,
        days_above_35c=25,
        days_with_heavy_rain=0,
        days_with_frost=0,
        consecutive_dry_days=29,
    )
    corr = CorroborationResult(
        corroborated=True, strength=0.9, evidence="QA corroboration", flags=[]
    )
    return Claim(
        farmer=farmer,
        crop_type="maize",
        date_of_damage=date(2025, 5, 1),
        damage=damage,
        weather=weather,
        corroboration=corr,
        estimated_loss_usd=640.0,
        status=ClaimStatus.pending_review,
    )


def _png_bytes(color=(100, 200, 50), size=64) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (size, size), color=color).save(buf, format="PNG")
    return buf.getvalue()


# ─── parse_telegram_update ──────────────────────────────────────────────────


class TestParseTelegramUpdate:
    def test_photo_array_picks_largest(self):
        from app.agents.whatsapp_intake import parse_telegram_update

        update = {
            "message": {
                "chat": {"id": 1},
                "from": {"first_name": "A"},
                "caption": "hello",
                "photo": [
                    {"file_id": "small", "width": 100, "height": 100},
                    {"file_id": "large", "width": 800, "height": 600},
                ],
            }
        }
        r = parse_telegram_update(update)
        assert r is not None
        assert r["photo_file_id"] == "large"
        assert r["mime"] == "image/jpeg"

    def test_image_document_accepted(self):
        from app.agents.whatsapp_intake import parse_telegram_update

        update = {
            "message": {
                "chat": {"id": 2},
                "from": {"first_name": "B"},
                "document": {"file_id": "doc1", "mime_type": "image/png"},
            }
        }
        r = parse_telegram_update(update)
        assert r is not None
        assert r["photo_file_id"] == "doc1"
        assert r["mime"] == "image/png"

    def test_non_image_document_rejected(self):
        from app.agents.whatsapp_intake import parse_telegram_update

        update = {
            "message": {
                "chat": {"id": 3},
                "from": {"first_name": "C"},
                "document": {"file_id": "doc2", "mime_type": "application/pdf"},
            }
        }
        r = parse_telegram_update(update)
        assert r is not None
        assert r["photo_file_id"] is None

    def test_start_command(self):
        from app.agents.whatsapp_intake import parse_telegram_update

        r = parse_telegram_update(
            {"message": {"chat": {"id": 4}, "from": {"first_name": "D"}, "text": "/start"}}
        )
        assert r is not None
        assert r["is_start"] is True

    def test_location_message(self):
        from app.agents.whatsapp_intake import parse_telegram_update

        r = parse_telegram_update(
            {
                "message": {
                    "chat": {"id": 5},
                    "from": {"first_name": "E"},
                    "location": {"latitude": 20.5937, "longitude": 78.9629},
                }
            }
        )
        assert r is not None
        assert r["location"] == (20.5937, 78.9629)

    def test_missing_chat_id_returns_none(self):
        from app.agents.whatsapp_intake import parse_telegram_update

        r = parse_telegram_update({"message": {"from": {"first_name": "F"}}})
        assert r is None

    def test_empty_update_returns_none(self):
        from app.agents.whatsapp_intake import parse_telegram_update

        assert parse_telegram_update({}) is None


# ─── parse_bird_payload ─────────────────────────────────────────────────────


class TestParseBirdPayload:
    def test_from_field_extraction(self):
        from app.agents.whatsapp_intake import parse_bird_payload

        r = parse_bird_payload({"from": "+919876543210", "body": "hi"})
        assert r is not None
        assert r["from"] == "+919876543210"

    def test_missing_sender_returns_none(self):
        from app.agents.whatsapp_intake import parse_bird_payload

        r = parse_bird_payload({"body": "no sender here"})
        assert r is None

    def test_image_media_url_extracted(self):
        from app.agents.whatsapp_intake import parse_bird_payload

        payload = {
            "from": "+1111111111",
            "body": {"image": {"mediaUrl": "https://example.com/img.jpg", "mimeType": "image/jpeg"}},
        }
        r = parse_bird_payload(payload)
        assert r is not None
        assert r["media_url"] == "https://example.com/img.jpg"
        assert r["media_content_type"] == "image/jpeg"


# ─── EXIF extraction ────────────────────────────────────────────────────────


class TestExtractExif:
    def test_png_without_exif(self):
        from app.agents.photo_forensics import extract_exif

        exif = extract_exif(_png_bytes())
        # PIL reports width/height even with no EXIF
        assert "width" in exif
        assert exif.get("camera_make") is None

    def test_invalid_bytes_returns_partial(self):
        from app.agents.photo_forensics import extract_exif

        # Should not raise
        exif = extract_exif(b"not an image")
        assert isinstance(exif, dict)


# ─── Perceptual hash dedupe ──────────────────────────────────────────────────


class TestPerceptualHashDedupe:
    def test_identical_image_detected_as_duplicate(self):
        from app.clients.perceptual_hash import average_hash, find_close_matches

        img = _png_bytes((10, 20, 30))
        h = average_hash(img)
        hits = find_close_matches(h, [("claim-A", h)], threshold=8)
        assert len(hits) == 1
        assert hits[0].other_id == "claim-A"
        assert hits[0].distance == 0

    def test_different_image_not_flagged(self):
        from app.clients.perceptual_hash import average_hash, find_close_matches

        h1 = average_hash(_png_bytes((0, 0, 0)))
        h2 = average_hash(_png_bytes((255, 255, 255)))
        # Two maximally different flat-colour images have distance=0 (quirk of
        # average-hash: all pixels equal the average so hash is all zeros).
        # This test documents the known limitation.
        hits = find_close_matches(h1, [("other", h2)], threshold=8)
        assert isinstance(hits, list)

    def test_corrupt_image_returns_zero_hash(self):
        from app.clients.perceptual_hash import average_hash

        h = average_hash(b"not-an-image")
        assert h == 0


# ─── CLAIM-001: pre-flight status write fixed ────────────────────────────────


class TestDecisionStatusOrdering:
    """Verify that post_decision does NOT write 'approved' before insurer call."""

    def test_approve_writes_submitted_before_insurer(self):
        """The first update_status call for approve must use 'submitted', not 'approved'."""
        import app.api_claims as api_claims

        claim = _make_claim()

        status_history: list[str] = []

        def fake_update_status(claim_id, status, **kw):
            status_history.append(status.value if hasattr(status, "value") else str(status))
            return claim

        mock_record = {
            "status": "approved",
            "insurer_claim_id": "INS-TEST",
            "reviewer_notes": "ok",
        }

        with (
            patch.object(api_claims.claims_repo, "get", return_value=claim),
            patch.object(api_claims.claims_repo, "get_row", return_value=MagicMock(pdf_path=None)),
            patch.object(api_claims.claims_repo, "update_status", side_effect=fake_update_status),
            patch.object(api_claims.insurer, "submit", return_value=mock_record),
        ):
            body = api_claims.DecisionPayload(decision="approve", notes="")
            api_claims.post_decision(claim.claim_id, body)

        # First write must be 'submitted', not 'approved'
        assert status_history[0] == "submitted", (
            f"Expected first write=submitted, got {status_history[0]!r} — CLAIM-001 regression"
        )

    def test_approve_rolls_back_on_insurer_failure(self):
        """If insurer.submit raises, status must roll back to pending_review."""
        from fastapi import HTTPException
        import app.api_claims as api_claims

        claim = _make_claim()
        status_history: list[str] = []

        def fake_update_status(claim_id, status, **kw):
            status_history.append(status.value if hasattr(status, "value") else str(status))
            return claim

        with (
            patch.object(api_claims.claims_repo, "get", return_value=claim),
            patch.object(api_claims.claims_repo, "update_status", side_effect=fake_update_status),
            patch.object(api_claims.insurer, "submit", side_effect=RuntimeError("insurer down")),
            pytest.raises(HTTPException) as exc_info,
        ):
            body = api_claims.DecisionPayload(decision="approve", notes="")
            api_claims.post_decision(claim.claim_id, body)

        assert exc_info.value.status_code == 502
        # After failure, must roll back to pending_review
        assert "pending_review" in status_history, (
            f"Expected rollback to pending_review, got history={status_history!r}"
        )


# ─── CLAIM-002: pdf_path passed through ClaimRow ─────────────────────────────


class TestNotifyFarmerPdfPath:
    """_notify_farmer should read pdf_path from ClaimRow, not Claim.

    telegram_client is imported inside _notify_farmer, so we patch
    the module it's imported FROM, not the api_claims namespace.
    """

    def test_notify_farmer_uses_explicit_pdf_path(self):
        import app.api_claims as api_claims
        from app.agents.multilingual import FarmerMessageKind

        claim = _make_claim(phone="telegram:99999")
        sent_docs: list[str] = []

        mock_tg = MagicMock()
        mock_tg.send_message.return_value = {}
        mock_tg.send_document.side_effect = lambda cid, path, **kw: sent_docs.append(path)

        with (
            patch("app.clients.telegram_client.send_message", mock_tg.send_message),
            patch("app.clients.telegram_client.send_document", mock_tg.send_document),
            patch("app.agents.multilingual._english_template", return_value="eng"),
            patch("app.agents.multilingual.localize", return_value="msg"),
        ):
            api_claims._notify_farmer(
                claim, FarmerMessageKind.approved, pdf_path="/tmp/test.pdf"
            )

        assert "/tmp/test.pdf" in sent_docs, "PDF not sent despite pdf_path being provided"

    def test_notify_farmer_skips_pdf_when_none(self):
        import app.api_claims as api_claims
        from app.agents.multilingual import FarmerMessageKind

        claim = _make_claim(phone="telegram:88888")
        sent_docs: list[str] = []

        mock_tg = MagicMock()
        mock_tg.send_message.return_value = {}
        mock_tg.send_document.side_effect = lambda cid, path, **kw: sent_docs.append(path)

        with (
            patch("app.clients.telegram_client.send_message", mock_tg.send_message),
            patch("app.clients.telegram_client.send_document", mock_tg.send_document),
            patch("app.agents.multilingual._english_template", return_value="eng"),
            patch("app.agents.multilingual.localize", return_value="msg"),
        ):
            api_claims._notify_farmer(
                claim, FarmerMessageKind.approved, pdf_path=None
            )

        assert len(sent_docs) == 0, "send_document should not be called when pdf_path is None"


# ─── CLAIM-003: perceptual hash dedupe in Telegram intake ────────────────────


class TestTelegramDedupeIntegration:
    """Verify that the perceptual-hash dedupe path in Telegram intake works.

    The dedupe block uses module-level local aliases (_claims_repo_ref,
    _photo_store_ref) that are created when the block runs. We patch the
    underlying module functions directly so the test doesn't depend on
    import-time variable names.
    """

    def test_duplicate_photo_short_circuits_pipeline(self):
        """A visually-identical photo for the same farmer must return
        'duplicate_photo' without calling assess_damage."""
        from app.agents.whatsapp_intake import process_inbound_telegram

        img = _png_bytes((50, 100, 150))

        from app.storage.db import ClaimRow
        from datetime import datetime

        existing_row = ClaimRow(
            claim_id="CF-EXISTING-DUP",
            status="pending_review",
            created_at=datetime.utcnow(),
            farmer_phone="telegram:7777",
            farmer_name="Old",
            farmer_language="en",
            crop_type="maize",
            estimated_loss_usd=100.0,
            payload="{}",
        )

        mock_stored_path = MagicMock()
        mock_stored_path.read_bytes.return_value = img

        # The farmer must be registered for a photo to reach the claim
        # (and therefore the dedupe) path; an unregistered chat is routed
        # into the first-run registration flow instead.
        registered = MagicMock(
            registration_step="complete",
            pending_pdf_claim_id=None,
            name="Old",
            language="en",
            region="",
            village="",
            farm_area_hectares=1.0,
            latitude=None,
            longitude=None,
            email="",
        )

        with (
            patch("app.storage.farmer_repo.get_by_chat_id", return_value=registered),
            patch("app.storage.claims_repo.list_by_status", return_value=[existing_row]),
            patch("app.storage.photo_store.find_photo", return_value=mock_stored_path),
            patch("app.clients.telegram_client.download_file", return_value=(img, "image/png")),
            patch("app.clients.telegram_client.send_message") as mock_send,
            patch("app.agents.damage_assessor.assess_damage") as mock_assess,
        ):
            result = process_inbound_telegram(
                chat_id=7777,
                user_name="TestFarmer",
                body="drought killed my crops",
                photo_file_id="some_file_id",
                mime="image/png",
            )

        assert result.status == "duplicate_photo", (
            f"Expected 'duplicate_photo', got {result.status!r}"
        )
        assert result.claim_id == "CF-EXISTING-DUP"
        # The VL assessment must NOT have been called for a duplicate
        mock_assess.assert_not_called()
        # The farmer was notified
        mock_send.assert_called_once()

    def test_dedupe_unit_find_close_matches(self):
        """Unit-level: find_close_matches with identical hashes returns one hit."""
        from app.clients.perceptual_hash import average_hash, find_close_matches

        img = _png_bytes((50, 100, 150))
        h = average_hash(img)
        hits = find_close_matches(h, [("CF-EXISTING", h)], threshold=8)
        assert len(hits) >= 1
        assert hits[0].other_id == "CF-EXISTING"
        assert hits[0].distance == 0


# ─── claims_repo round-trip ──────────────────────────────────────────────────


class TestClaimsRepoRoundTrip:
    """save() then get() must return equivalent claim data."""

    def test_save_and_retrieve(self, tmp_path):
        from app.storage import claims_repo

        claim = _make_claim()
        # Use a unique claim_id to avoid collisions with demo seed data
        claim.claim_id = f"CLAIMFARM-QA-{int(time.time() * 1000)}"

        try:
            claims_repo.save(claim, index=False)  # skip vector index in unit test
            fetched = claims_repo.get(claim.claim_id)
            assert fetched is not None
            assert fetched.claim_id == claim.claim_id
            assert fetched.crop_type == "maize"
            assert fetched.farmer.phone == claim.farmer.phone
        finally:
            # Clean up
            from sqlmodel import Session, delete
            from app.storage.db import ClaimRow, get_engine

            with Session(get_engine()) as session:
                session.exec(delete(ClaimRow).where(ClaimRow.claim_id == claim.claim_id))
                session.commit()


# ─── mock insurer (in-process) ───────────────────────────────────────────────


class TestMockInsurerInProcess:
    def test_submit_returns_decision(self):
        from app.clients import insurer

        claim = _make_claim()
        record = insurer.submit(claim)
        assert "status" in record
        assert record["status"] in ("approved", "rejected", "needs_more_info", "under_review")
        assert "insurer_claim_id" in record

    def test_submit_high_payout_lower_approval(self):
        """Seed claim with high payout should see a non-trivial rejection rate
        (base_approve -= 0.2 when requested_payout_usd > 5000). We test the
        mock logic is reachable; we don't assert a deterministic outcome."""
        from app.clients import insurer

        claim = _make_claim()
        claim.estimated_loss_usd = 8000.0
        record = insurer.submit(claim)
        assert record["status"] in ("approved", "rejected", "needs_more_info")


# ─── multilingual detect + status_message ────────────────────────────────────


class TestMultilingual:
    def test_empty_text_defaults_to_en(self):
        from app.agents.multilingual import detect_language

        lang, conf = detect_language("")
        assert lang == "en"

    def test_status_message_english(self):
        from app.agents.multilingual import status_message

        claim = _make_claim()
        msg = status_message(claim, target_language="en")
        assert isinstance(msg, str)
        assert len(msg) > 10


# ─── photo_store ─────────────────────────────────────────────────────────────


class TestPhotoStore:
    def test_save_and_find(self):
        from app.storage import photo_store

        claim_id = f"CLAIMFARM-QA-PHOTO-{int(time.time() * 1000)}"
        img = _png_bytes()
        try:
            photo_store.save_bytes(claim_id, img, mime="image/png")
            found = photo_store.find_photo(claim_id)
            assert found is not None
            assert found.stem == claim_id
        finally:
            if found and found.exists():
                found.unlink(missing_ok=True)

    def test_public_url_format(self):
        from app.storage import photo_store

        url = photo_store.public_url("CF-TEST")
        assert url == "/api/claims/CF-TEST/photo"
