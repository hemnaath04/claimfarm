"""Process an inbound WhatsApp message end-to-end:
photo -> damage -> weather -> claim -> PDF -> DB -> localized reply.
"""

from __future__ import annotations

import base64
import logging
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from typing import Any

from app.agents.claim_drafter import build_claim, render_claim_pdf
from app.agents.damage_assessor import assess_damage
from app.agents.multilingual import detect_language, status_message
from app.agents.weather_corroborator import corroborate
from app.clients import bird_client, notifications, telegram_client, twilio_client
from app.models.claim import ClaimStatus, Farmer
from app.storage import claims_repo, farmer_profiles, farmer_repo

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


_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _looks_like_email(text: str) -> bool:
    return bool(_EMAIL_RE.match((text or "").strip()))


def _parse_farm_size(text: str) -> float | None:
    """Pull a hectare figure out of free text like '2', '2.5 ha', '1,5'."""
    cleaned = (text or "").strip().lower().replace(",", ".")
    m = re.search(r"\d+(?:\.\d+)?", cleaned)
    if not m:
        return None
    try:
        value = float(m.group(0))
    except ValueError:
        return None
    return value if value > 0 else None


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
    """Extract a normalized payload from a Telegram webhook update.

    Two shapes are returned. For an inline-button tap (`callback_query`) the
    `callback_data` / `callback_query_id` keys are populated and the message
    fields are None. For a normal message they're the reverse, with
    `callback_data` explicitly None so the caller can branch on it.
    """
    cq = update.get("callback_query")
    if isinstance(cq, dict):
        chat_id = (((cq.get("message") or {}).get("chat")) or {}).get("id")
        if chat_id is None:
            return None
        return {
            "chat_id": chat_id,
            "user_name": ((cq.get("from") or {}).get("first_name") or str(chat_id)),
            "body": "",
            "photo_file_id": None,
            "mime": None,
            "location": None,
            "is_start": False,
            "callback_data": cq.get("data"),
            "callback_query_id": cq.get("id"),
        }

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
        "callback_data": None,
        "callback_query_id": None,
    }


# Telegram registration prompts, keyed by the step we transition INTO.
_REG_LANGUAGE_NAMES = {
    "en": "English",
    "hi": "हिन्दी",
    "es": "Español",
    "fr": "Français",
    "ar": "العربية",
    "zh": "中文",
}


def _send(chat_id: int, text: str, **kwargs) -> None:
    """Best-effort send: a transport error must never crash the webhook task."""
    try:
        telegram_client.send_message(chat_id, text, **kwargs)
    except Exception:
        logger.exception("telegram send_message failed")


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
    """Drive first-run registration, then the claim pipeline, over Telegram.

    A farmer must register (name → language → location → village → crops →
    farm size → email) before they can file a claim. The current position is
    persisted on `FarmerProfileRow.registration_step`; each inbound message
    advances exactly one step. Once `registration_step == "complete"`, photos
    flow into the existing assess/build/persist pipeline.
    """
    key = str(chat_id)
    profile = farmer_repo.get_by_chat_id(key)

    # First contact (or explicit /start) — create the profile and welcome them.
    if profile is None or is_start:
        profile = farmer_repo.get_or_create(
            key,
            phone=f"telegram:{chat_id}",
            name=user_name or "",
            registration_step="awaiting_name",
        )
        if is_start:
            farmer_repo.update(key, registration_step="awaiting_name")
        _send(
            chat_id,
            "🌱 Welcome to ClaimFarm. Crop-insurance claims by photo, in your "
            "own language.\n\n"
            "Let's set up your account first (takes under a minute). "
            "What's your name?",
            reply_markup=telegram_client.remove_keyboard(),
        )
        return IntakeResult(claim_id=None, status="awaiting_name")

    step = profile.registration_step or "new"

    # A pending PDF email request takes priority over the claim pipeline: the
    # farmer tapped "email me a copy" but had no address on file, so the next
    # email-shaped message should complete that send (Phase 4 fallback).
    if profile.pending_pdf_claim_id and step == "complete":
        if _looks_like_email(body):
            email = body.strip()
            farmer_repo.update(key, email=email)
            claim_id = profile.pending_pdf_claim_id
            ok = _email_claim_pdf(claim_id=claim_id, to=email, farmer_name=profile.name)
            farmer_repo.set_pending_pdf(key, None)
            _send(
                chat_id,
                f"Sent to {email} ✅" if ok
                else "Sorry, I couldn't send that PDF. Please try again later.",
            )
            return IntakeResult(claim_id=claim_id, status="pdf_emailed" if ok else "pdf_email_failed")
        # Not an email — fall through so a photo can still file a claim, but
        # nudge text-only messages back to providing an address.
        if not photo_file_id and location is None:
            _send(chat_id, "Please send a valid email address (or send a photo to file a new claim).")
            return IntakeResult(claim_id=None, status="awaiting_pdf_email")

    # ----- registration state machine -----
    if step in ("new", "awaiting_name"):
        # `new` only happens for legacy rows; treat the message as their name.
        if step == "new":
            farmer_repo.update(key, registration_step="awaiting_name")
        name = (body or "").strip() or user_name or f"tg-{chat_id}"
        farmer_repo.update(key, name=name, registration_step="awaiting_language")
        _send(
            chat_id,
            f"Thanks, {name}! Which language should I reply in? "
            "Tap below or just type it.",
            reply_markup=telegram_client.language_inline_keyboard(),
        )
        return IntakeResult(claim_id=None, status="awaiting_language")

    if step == "awaiting_language":
        return _advance_language(chat_id=chat_id, key=key, raw=body)

    if step == "awaiting_location":
        if location is not None:
            lat, lon = location
            farmer_repo.update(key, latitude=lat, longitude=lon)
            farmer_profiles.set_location(chat_id, lat, lon, name=profile.name or "")
        # `location is None` (or a typed "skip") just advances without coords.
        farmer_repo.update(key, registration_step="awaiting_village")
        _send(
            chat_id,
            "Got it. What village or area is your farm in?",
            reply_markup=telegram_client.remove_keyboard(),
        )
        return IntakeResult(claim_id=None, status="awaiting_village")

    if step == "awaiting_village":
        village = (body or "").strip()
        fields: dict[str, Any] = {"village": village, "registration_step": "awaiting_crops"}
        if village and not (profile.region or "").strip():
            fields["region"] = village
        farmer_repo.update(key, **fields)
        _send(chat_id, "What's your primary crop (or crops)?")
        return IntakeResult(claim_id=None, status="awaiting_crops")

    if step == "awaiting_crops":
        farmer_repo.update(
            key, crops=(body or "").strip(), registration_step="awaiting_farm_size"
        )
        _send(chat_id, "Roughly how large is your farm, in hectares? (e.g. 2.5)")
        return IntakeResult(claim_id=None, status="awaiting_farm_size")

    if step == "awaiting_farm_size":
        size = _parse_farm_size(body)
        if size is None:
            _send(chat_id, "Sorry, I didn't catch a number. How many hectares? (e.g. 2 or 2.5)")
            return IntakeResult(claim_id=None, status="awaiting_farm_size")
        farmer_repo.update(
            key, farm_area_hectares=size, registration_step="awaiting_email"
        )
        _send(
            chat_id,
            "Last step: what email should I send PDF copies of your claims to? "
            'Type an address, or "skip".',
        )
        return IntakeResult(claim_id=None, status="awaiting_email")

    if step == "awaiting_email":
        text = (body or "").strip()
        if text and text.lower() != "skip":
            if _looks_like_email(text):
                farmer_repo.update(key, email=text)
            else:
                _send(chat_id, 'That doesn\'t look like an email. Type a valid address, or "skip".')
                return IntakeResult(claim_id=None, status="awaiting_email")
        farmer_repo.update(key, registration_step="complete")
        _send(
            chat_id,
            "You're all set! 🌱 Now send a photo of the damaged crop (with a "
            "short caption) to file a claim.",
        )
        return IntakeResult(claim_id=None, status="registration_complete")

    # ----- step == "complete": the claim pipeline -----
    if location is not None:
        # Let a registered farmer refine their saved location at any time.
        lat, lon = location
        farmer_repo.update(key, latitude=lat, longitude=lon)
        farmer_profiles.set_location(chat_id, lat, lon, name=profile.name or "")
        _send(
            chat_id,
            f"Updated your farm location ({lat:.4f}, {lon:.4f}). Send a photo of "
            "the damaged crop to file a claim.",
            reply_markup=telegram_client.remove_keyboard(),
        )
        return IntakeResult(claim_id=None, status="location_saved")

    if not photo_file_id:
        _send(
            chat_id,
            "Send a photo of your damaged crop (with a short caption describing "
            "what happened) and I'll file an insurance claim for you.",
        )
        return IntakeResult(claim_id=None, status="awaiting_photo")

    return _file_telegram_claim(
        chat_id=chat_id,
        profile=profile,
        body=body,
        photo_file_id=photo_file_id,
        mime=mime,
    )


def _advance_language(*, chat_id: int, key: str, raw: str) -> IntakeResult:
    """Save the chosen language and move on to the location step. Accepts a
    `lang:xx` callback payload, a bare code, or a typed language name."""
    raw = (raw or "").strip()
    code = "en"
    if raw.lower().startswith("lang:"):
        code = raw.split(":", 1)[1].strip().lower() or "en"
    elif raw.lower() in _REG_LANGUAGE_NAMES:
        code = raw.lower()
    else:
        # Typed language name or free text — best-effort detection.
        lowered = raw.lower()
        for c, name in _REG_LANGUAGE_NAMES.items():
            if name.lower() == lowered or c == lowered:
                code = c
                break
        else:
            if raw:
                detected, _ = detect_language(raw)
                code = detected or "en"
    if code not in _REG_LANGUAGE_NAMES:
        code = "en"
    farmer_repo.update(key, language=code, registration_step="awaiting_location")
    _send(
        chat_id,
        "Great. Tap below to share your farm location (used for weather "
        'verification), or type "skip".',
        reply_markup=telegram_client.location_request_keyboard(),
    )
    return IntakeResult(claim_id=None, status="awaiting_location")


def _file_telegram_claim(
    *,
    chat_id: int,
    profile,
    body: str,
    photo_file_id: str,
    mime: str | None,
) -> IntakeResult:
    """Assess a photo and persist a claim, populating the Farmer from the
    registered profile (falling back to demo defaults for empty fields)."""
    lang = (profile.language or "").strip() or (
        detect_language(body)[0] if body else "en"
    )

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

    # Perceptual-hash dedupe: reject photos that are visually identical to a
    # claim already in the queue from this same chat. We compare against all
    # stored photos for the farmer's phone identifier so even a re-submit from
    # a new session is caught. This runs BEFORE the expensive Qwen-VL call.
    from app.clients.perceptual_hash import average_hash, find_close_matches
    from app.storage import photo_store as _photo_store_ref
    from app.storage import claims_repo as _claims_repo_ref

    try:
        incoming_hash = average_hash(photo_bytes)
        # Build corpus: (claim_id, hash) for all photos on file for this farmer.
        farmer_phone_key = f"telegram:{chat_id}"
        existing_rows = _claims_repo_ref.list_by_status()
        corpus: list[tuple[str, int]] = []
        for row in existing_rows:
            if row.farmer_phone != farmer_phone_key:
                continue
            stored = _photo_store_ref.read_bytes(row.claim_id)
            if stored is None:
                continue
            try:
                corpus.append((row.claim_id, average_hash(stored[0])))
            except Exception:
                logger.debug("could not hash stored photo for %s", row.claim_id)
        close = find_close_matches(incoming_hash, corpus, threshold=8)
        if close:
            dup_id = close[0].other_id
            logger.warning(
                "telegram dedupe: photo from chat %s matches existing claim %s (dist=%d)",
                chat_id, dup_id, close[0].distance,
            )
            try:
                telegram_client.send_message(
                    chat_id,
                    f"We noticed this photo matches a claim you already submitted "
                    f"({dup_id}). If you meant to file a new claim, please send a "
                    "different photo of the damage.",
                )
            except Exception:
                logger.exception("telegram send_message (dedupe path) failed")
            return IntakeResult(claim_id=dup_id, status="duplicate_photo")
    except Exception:
        # Dedupe failure must never block claim processing.
        logger.exception("perceptual hash dedupe failed; continuing")

    # Run damage + forensics + weather + draft. Any failure here (e.g. a
    # missing model API key, an upstream timeout) must not silently kill the
    # background task — the farmer should always get a reply, and the error
    # must be logged for the operator.
    from app.agents import photo_forensics  # local import to keep startup light

    try:
        damage = assess_damage(image_data_url)
        forensics = photo_forensics.analyze(photo_bytes, image_data_url)

        # Location precedence: registered/shared farm location → EXIF GPS →
        # demo default. The profile carries the location captured at sign-up.
        if profile.latitude is not None and profile.longitude is not None:
            lat, lon = profile.latitude, profile.longitude
        else:
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

        weather, corr = corroborate(
            damage, latitude=lat, longitude=lon, claim_date=claim_date
        )

        farmer = Farmer(
            name=(profile.name or "").strip() or f"tg-{chat_id}",
            phone=f"telegram:{chat_id}",
            language=lang,
            latitude=lat,
            longitude=lon,
            region=(profile.region or "").strip()
            or (profile.village or "").strip()
            or DEFAULT_REGION,
            farm_area_hectares=profile.farm_area_hectares or DEFAULT_FARM_AREA_HA,
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
    except Exception as exc:  # noqa: BLE001
        logger.exception("telegram claim assessment failed")
        try:
            telegram_client.send_message(
                chat_id,
                "Sorry, something went wrong assessing your photo. Our team "
                "has been notified. Please try again in a few minutes.",
            )
        except Exception:
            logger.exception("telegram send_message (assess-fail path) failed")
        return IntakeResult(
            claim_id=None, status="assessment_failed", detail=str(exc)
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
        pdf_path = render_claim_pdf(claim, f"/tmp/{claim.claim_id}.pdf")
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


def _email_claim_pdf(*, claim_id: str, to: str, farmer_name: str) -> bool:
    """Rebuild the claim PDF from the stored claim and email it. Returns True on
    a delivered send, False on any failure.

    We regenerate rather than read a saved file: the container app dir isn't
    writable on FC and /tmp is per-instance, so the only durable source is the
    claim record itself (DB). Rendering into writable /tmp always works.
    """
    try:
        claim = claims_repo.get(claim_id)
        if claim is None:
            logger.warning("pdf email: no claim for %s", claim_id)
            return False
        pdf_path = render_claim_pdf(claim, f"/tmp/{claim_id}.pdf")
        pdf_bytes = Path(pdf_path).read_bytes()
        result = notifications.send_claim_pdf_email(
            to=to, claim_id=claim_id, farmer_name=farmer_name or "", pdf_bytes=pdf_bytes
        )
        return bool(result.delivered)
    except Exception:
        logger.exception("pdf email failed for %s", claim_id)
        return False


def process_telegram_callback(
    *,
    chat_id: int,
    user_name: str,
    data: str | None,
    callback_query_id: str | None,
) -> IntakeResult:
    """Handle an inline-button tap: language choice during registration, or a
    "email me a PDF" request after a claim decision."""
    key = str(chat_id)
    data = (data or "").strip()

    # Always stop the client's loading spinner, regardless of outcome.
    if callback_query_id:
        try:
            telegram_client.answer_callback_query(callback_query_id)
        except Exception:
            logger.exception("telegram answerCallbackQuery failed")

    # Language selection during registration.
    if data.startswith("lang:"):
        profile = farmer_repo.get_by_chat_id(key)
        if profile is None:
            # Tapped a stale button before registering — start fresh.
            return process_inbound_telegram(
                chat_id=chat_id, user_name=user_name, body="", photo_file_id=None,
                mime=None, location=None, is_start=True,
            )
        return _advance_language(chat_id=chat_id, key=key, raw=data)

    # "No thanks" on the PDF offer.
    if data == "pdf:no":
        _send(chat_id, "No problem.")
        return IntakeResult(claim_id=None, status="pdf_declined")

    # "Email me a PDF copy" on a decided claim.
    if data.startswith("pdf:"):
        claim_id = data.split(":", 1)[1].strip()
        profile = farmer_repo.get_by_chat_id(key)
        email = (profile.email or "").strip() if profile else ""
        if email:
            ok = _email_claim_pdf(
                claim_id=claim_id, to=email, farmer_name=(profile.name if profile else "") or ""
            )
            _send(
                chat_id,
                f"Sent to {email} ✅" if ok
                else "Sorry, I couldn't send that PDF. Please try again later.",
            )
            return IntakeResult(claim_id=claim_id, status="pdf_emailed" if ok else "pdf_email_failed")
        # No email on file — stash the claim and ask for one.
        farmer_repo.set_pending_pdf(key, claim_id)
        _send(chat_id, "What email should I send it to?")
        return IntakeResult(claim_id=claim_id, status="awaiting_pdf_email")

    logger.warning("telegram callback: unhandled data %r", data)
    return IntakeResult(claim_id=None, status="callback_ignored")
