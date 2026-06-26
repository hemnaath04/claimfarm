"""Process an inbound WhatsApp message end-to-end:
photo -> damage -> weather -> claim -> PDF -> DB -> localized reply.
"""

from __future__ import annotations

import base64
import logging
from dataclasses import dataclass
from datetime import date

from typing import Any

from app.agents.claim_drafter import build_claim, render_claim_pdf
from app.agents.damage_assessor import assess_damage
from app.agents.multilingual import detect_language, status_message
from app.agents.weather_corroborator import corroborate
from app.clients import bird_client, telegram_client, twilio_client
from app.models.claim import ClaimStatus, Farmer
from app.storage import claims_repo, farmer_profiles

logger = logging.getLogger(__name__)

# Default GPS for demo when the farmer doesn't share location.
# A real deployment would require an opt-in location share or a registration step.
DEFAULT_LATITUDE = 20.5937
DEFAULT_LONGITUDE = 78.9629
DEFAULT_REGION = "via WhatsApp"
DEFAULT_FARM_AREA_HA = 1.0


@dataclass
class IntakeResult:
    claim_id: str | None
    status: str
    detail: str = ""


def process_inbound(
    *,
    from_phone: str,
    body: str,
    media_url: str | None,
    media_content_type: str | None,
) -> IntakeResult:
    """Run the full ClaimFarm pipeline on a Twilio webhook payload."""
    if not media_url:
        twilio_client.send_whatsapp(
            from_phone,
            "Please send a photo of the damaged crop, along with a short "
            "description of what happened, and we'll start your claim.",
        )
        return IntakeResult(claim_id=None, status="awaiting_photo")

    lang, _ = detect_language(body) if body else ("en", 0.0)

    try:
        photo_bytes = twilio_client.download_media(media_url)
    except Exception as exc:  # noqa: BLE001
        logger.exception("media download failed")
        twilio_client.send_whatsapp(
            from_phone,
            "We could not download the photo. Please try sending it again.",
        )
        return IntakeResult(claim_id=None, status="media_download_failed", detail=str(exc))

    mime = media_content_type or "image/jpeg"
    image_data_url = "data:" + mime + ";base64," + base64.b64encode(photo_bytes).decode("ascii")

    damage = assess_damage(image_data_url)
    weather, corr = corroborate(
        damage,
        latitude=DEFAULT_LATITUDE,
        longitude=DEFAULT_LONGITUDE,
        claim_date=date.today(),
    )

    bare_phone = from_phone.replace("whatsapp:", "").strip()
    farmer = Farmer(
        name=bare_phone,  # we don't have a name yet; phone stands in
        phone=bare_phone,
        language=lang,
        latitude=DEFAULT_LATITUDE,
        longitude=DEFAULT_LONGITUDE,
        region=DEFAULT_REGION,
        farm_area_hectares=DEFAULT_FARM_AREA_HA,
    )

    claim = build_claim(
        farmer=farmer,
        damage=damage,
        weather=weather,
        corroboration=corr,
        date_of_damage=date.today(),
        farmer_narrative=body or "",
    )

    try:
        pdf_path = render_claim_pdf(claim, f"data/pdfs/{claim.claim_id}.pdf")
        claims_repo.save(claim, pdf_path=str(pdf_path))
    except Exception:  # noqa: BLE001
        logger.exception("claim persistence failed")
        # Continue anyway — the farmer should still get a response
        claims_repo.save(claim)

    claim.status = ClaimStatus.pending_review
    reply = status_message(claim, target_language=lang)
    twilio_client.send_whatsapp(from_phone, reply)
    return IntakeResult(claim_id=claim.claim_id, status="processed")


# ---------------------------------------------------------------------------
# Bird (MessageBird) variant
# ---------------------------------------------------------------------------


def _first(d: Any, *keys: str) -> Any:
    """Return the first non-empty value walking nested dict keys."""
    for k in keys:
        if isinstance(d, dict) and d.get(k) not in (None, "", [], {}):
            return d[k]
    return None


def parse_bird_payload(payload: dict) -> dict | None:
    """Best-effort extraction of (from, body, media_url, media_content_type)
    from Bird's WhatsApp webhook JSON. Bird's exact schema varies across
    workspace versions, so we walk a few common shapes.
    """
    # Some Bird tenants wrap the actual message under a 'payload' or 'event' key
    for top in ("payload", "event", "data"):
        if isinstance(payload, dict) and isinstance(payload.get(top), dict):
            payload = payload[top]
            break

    # Sender phone — try several common locations
    from_phone = (
        _first(payload, "from", "sender", "msisdn", "phoneNumber")
        or _first(payload.get("contact") or {}, "phoneNumber", "msisdn")
        or _first(payload.get("originator") or {}, "phoneNumber", "msisdn")
    )
    if isinstance(from_phone, dict):
        from_phone = (
            from_phone.get("identifierValue")
            or from_phone.get("phoneNumber")
            or from_phone.get("msisdn")
        )

    body = payload.get("body") if isinstance(payload.get("body"), str) else None
    if not body:
        body_obj = payload.get("body") if isinstance(payload.get("body"), dict) else {}
        body = (
            (body_obj.get("text") or {}).get("text")
            if isinstance(body_obj.get("text"), dict)
            else body_obj.get("text")
        ) or payload.get("text") or ""

    # Media URL — covers image / attachment / mediaItems shapes
    media_url = None
    media_type = None
    body_obj = payload.get("body") if isinstance(payload.get("body"), dict) else {}
    for media_key in ("image", "video", "document", "file", "audio"):
        block = body_obj.get(media_key)
        if isinstance(block, dict):
            media_url = (
                block.get("mediaUrl")
                or block.get("url")
                or block.get("href")
                or block.get("link")
            )
            media_type = block.get("mimeType") or block.get("contentType")
            if media_url:
                break

    if not media_url:
        for arr_key in ("attachments", "mediaItems", "media"):
            arr = payload.get(arr_key)
            if isinstance(arr, list) and arr:
                item = arr[0]
                if isinstance(item, dict):
                    media_url = (
                        item.get("url")
                        or item.get("mediaUrl")
                        or item.get("href")
                    )
                    media_type = item.get("mimeType") or item.get("contentType")
                    if media_url:
                        break

    if not from_phone:
        logger.warning("bird payload: could not find sender phone in %s", list(payload.keys()))
        return None

    return {
        "from": str(from_phone),
        "body": str(body or ""),
        "media_url": media_url,
        "media_content_type": media_type,
    }


def process_inbound_bird(
    *,
    from_phone: str,
    body: str,
    media_url: str | None,
    media_content_type: str | None,
) -> IntakeResult:
    """Same pipeline as `process_inbound`, but replies via Bird's API."""
    if not media_url:
        try:
            bird_client.send_whatsapp(
                from_phone,
                "Please send a photo of the damaged crop, along with a short "
                "description of what happened, and we'll start your claim.",
            )
        except Exception:
            logger.exception("bird send_whatsapp (no-media path) failed")
        return IntakeResult(claim_id=None, status="awaiting_photo")

    lang, _ = detect_language(body) if body else ("en", 0.0)

    try:
        photo_bytes = bird_client.download_media(media_url)
    except Exception as exc:  # noqa: BLE001
        logger.exception("bird media download failed")
        try:
            bird_client.send_whatsapp(
                from_phone,
                "We could not download the photo. Please try sending it again.",
            )
        except Exception:
            logger.exception("bird send_whatsapp (media-fail path) failed")
        return IntakeResult(claim_id=None, status="media_download_failed", detail=str(exc))

    mime = media_content_type or "image/jpeg"
    image_data_url = "data:" + mime + ";base64," + base64.b64encode(photo_bytes).decode("ascii")

    damage = assess_damage(image_data_url)
    weather, corr = corroborate(
        damage,
        latitude=DEFAULT_LATITUDE,
        longitude=DEFAULT_LONGITUDE,
        claim_date=date.today(),
    )

    bare = from_phone.replace("whatsapp:", "").strip()
    farmer = Farmer(
        name=bare,
        phone=bare,
        language=lang,
        latitude=DEFAULT_LATITUDE,
        longitude=DEFAULT_LONGITUDE,
        region=DEFAULT_REGION,
        farm_area_hectares=DEFAULT_FARM_AREA_HA,
    )

    claim = build_claim(
        farmer=farmer,
        damage=damage,
        weather=weather,
        corroboration=corr,
        date_of_damage=date.today(),
        farmer_narrative=body or "",
    )

    try:
        pdf_path = render_claim_pdf(claim, f"data/pdfs/{claim.claim_id}.pdf")
        claims_repo.save(claim, pdf_path=str(pdf_path))
    except Exception:
        logger.exception("claim persistence failed (bird path)")
        claims_repo.save(claim)

    claim.status = ClaimStatus.pending_review
    reply = status_message(claim, target_language=lang)
    try:
        bird_client.send_whatsapp(from_phone, reply)
    except Exception:
        logger.exception("bird send_whatsapp (reply) failed")
    return IntakeResult(claim_id=claim.claim_id, status="processed")


# ---------------------------------------------------------------------------
# Telegram variant
# ---------------------------------------------------------------------------


def parse_telegram_update(update: dict) -> dict | None:
    """Extract (chat_id, body, photo_file_id, mime, location, is_start) from a
    Telegram webhook update."""
    msg = update.get("message") or update.get("edited_message")
    if not msg:
        return None

    chat_id = (msg.get("chat") or {}).get("id")
    if chat_id is None:
        return None

    body = msg.get("caption") or msg.get("text") or ""

    photo_file_id = None
    mime = None
    # Telegram's `photo` is an array of progressively larger sizes; pick the largest.
    photos = msg.get("photo")
    if isinstance(photos, list) and photos:
        photo_file_id = photos[-1].get("file_id")
        mime = "image/jpeg"

    # `document` covers image attachments sent uncompressed
    if not photo_file_id:
        doc = msg.get("document")
        if isinstance(doc, dict):
            doc_mime = (doc.get("mime_type") or "").lower()
            if doc_mime.startswith("image/"):
                photo_file_id = doc.get("file_id")
                mime = doc_mime

    loc = msg.get("location") if isinstance(msg.get("location"), dict) else None
    location = None
    if loc and "latitude" in loc and "longitude" in loc:
        location = (float(loc["latitude"]), float(loc["longitude"]))

    is_start = isinstance(body, str) and body.strip().lower().startswith("/start")

    return {
        "chat_id": chat_id,
        "user_name": ((msg.get("from") or {}).get("first_name") or str(chat_id)),
        "body": body,
        "photo_file_id": photo_file_id,
        "mime": mime,
        "location": location,
        "is_start": is_start,
    }


def process_inbound_telegram(
    *,
    chat_id: int,
    user_name: str,
    body: str,
    photo_file_id: str | None,
    mime: str | None,
    location: tuple[float, float] | None = None,
    is_start: bool = False,
) -> IntakeResult:
    """Same pipeline as the WhatsApp variants, but via Telegram Bot API."""
    # /start — onboarding message with a location-request keyboard
    if is_start:
        try:
            telegram_client.send_message(
                chat_id,
                "Hi! I'm ClaimFarm. To file a crop-insurance claim:\n\n"
                "1) Tap the button below to share your farm location (used for "
                "weather verification).\n"
                "2) Then send a photo of the damaged crop with a short caption "
                "in any language.\n\n"
                "If you skip step 1, I'll still process the claim but use your "
                "photo's GPS metadata (if any).",
                reply_markup=telegram_client.location_request_keyboard(),
            )
        except Exception:
            logger.exception("telegram /start onboarding failed")
        return IntakeResult(claim_id=None, status="started")

    # Location share — persist and acknowledge
    if location is not None:
        lat, lon = location
        farmer_profiles.set_location(chat_id, lat, lon, name=user_name or "")
        try:
            telegram_client.send_message(
                chat_id,
                f"Got your location ({lat:.4f}, {lon:.4f}). Now send a photo "
                "of the damaged crop with a short caption.",
                reply_markup=telegram_client.remove_keyboard(),
            )
        except Exception:
            logger.exception("telegram location ack failed")
        return IntakeResult(claim_id=None, status="location_saved")

    if not photo_file_id:
        try:
            telegram_client.send_message(
                chat_id,
                "Hi! Send a photo of your damaged crop (with a short caption "
                "describing what happened) and I'll file an insurance claim "
                "for you.",
            )
        except Exception:
            logger.exception("telegram send_message (no-media path) failed")
        return IntakeResult(claim_id=None, status="awaiting_photo")

    lang, _ = detect_language(body) if body else ("en", 0.0)

    try:
        photo_bytes, resolved_mime = telegram_client.download_file(photo_file_id)
    except Exception as exc:  # noqa: BLE001
        logger.exception("telegram download_file failed")
        try:
            telegram_client.send_message(
                chat_id, "Could not download that photo. Please send it again."
            )
        except Exception:
            logger.exception("telegram send_message (media-fail path) failed")
        return IntakeResult(claim_id=None, status="media_download_failed", detail=str(exc))

    image_mime = mime or resolved_mime or "image/jpeg"
    image_data_url = (
        "data:" + image_mime + ";base64," + base64.b64encode(photo_bytes).decode("ascii")
    )

    # Run damage + forensics. Forensics gives us EXIF-derived GPS and capture
    # time that we prefer over the hardcoded demo defaults when present.
    from app.agents import photo_forensics  # local import to keep startup light

    damage = assess_damage(image_data_url)
    forensics = photo_forensics.analyze(photo_bytes, image_data_url)

    # Location precedence: explicitly-shared farm location → EXIF GPS → demo default.
    saved = farmer_profiles.get_location(chat_id)
    if saved is not None:
        lat, lon = saved
    elif forensics.gps_lat is not None and forensics.gps_lon is not None:
        lat, lon = forensics.gps_lat, forensics.gps_lon
    else:
        lat, lon = DEFAULT_LATITUDE, DEFAULT_LONGITUDE
    claim_date = (
        forensics.capture_time.date()
        if forensics.capture_time is not None
        else date.today()
    )

    weather, corr = corroborate(damage, latitude=lat, longitude=lon, claim_date=claim_date)

    farmer = Farmer(
        name=user_name or f"tg-{chat_id}",
        phone=f"telegram:{chat_id}",
        language=lang,
        latitude=lat,
        longitude=lon,
        region=DEFAULT_REGION,
        farm_area_hectares=DEFAULT_FARM_AREA_HA,
    )

    claim = build_claim(
        farmer=farmer,
        damage=damage,
        weather=weather,
        corroboration=corr,
        date_of_damage=claim_date,
        farmer_narrative=body or "",
        forensics=forensics,
    )

    # Persist the photo bytes under the claim_id so the adjuster console can
    # render them. Attach a public reference to photo_urls. We deliberately
    # save AFTER build_claim so the path is keyed by the final claim_id.
    try:
        from app.storage import photo_store

        photo_store.save_bytes(claim.claim_id, photo_bytes, mime=image_mime)
        claim.photo_urls = [photo_store.public_url(claim.claim_id)]
    except Exception:
        logger.exception("photo persistence failed (telegram path)")

    try:
        pdf_path = render_claim_pdf(claim, f"data/pdfs/{claim.claim_id}.pdf")
        claims_repo.save(claim, pdf_path=str(pdf_path))
    except Exception:
        logger.exception("claim persistence failed (telegram path)")
        claims_repo.save(claim)

    claim.status = ClaimStatus.pending_review
    reply = status_message(claim, target_language=lang)
    try:
        telegram_client.send_message(chat_id, reply)
    except Exception:
        logger.exception("telegram send_message (reply) failed")
    return IntakeResult(claim_id=claim.claim_id, status="processed")
