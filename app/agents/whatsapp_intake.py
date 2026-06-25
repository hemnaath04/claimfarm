"""Process an inbound WhatsApp message end-to-end:
photo -> damage -> weather -> claim -> PDF -> DB -> localized reply.
"""

from __future__ import annotations

import base64
import logging
from dataclasses import dataclass
from datetime import date

from app.agents.claim_drafter import build_claim, render_claim_pdf
from app.agents.damage_assessor import assess_damage
from app.agents.multilingual import detect_language, status_message
from app.agents.weather_corroborator import corroborate
from app.clients import twilio_client
from app.models.claim import ClaimStatus, Farmer
from app.storage import claims_repo

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
