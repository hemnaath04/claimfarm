"""Language detection + localized reply generation via Qwen-Max."""

from __future__ import annotations

import json
from enum import Enum

from app.clients.qwen import text_chat
from app.models.claim import Claim, ClaimStatus

SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "bn": "Bengali",
    "sw": "Swahili",
    "es": "Spanish",
    "pt": "Portuguese (Brazilian)",
    "fr": "French",
    "ar": "Arabic",
    "zh": "Chinese (Simplified)",
    "id": "Indonesian",
}


class FarmerMessageKind(str, Enum):
    received = "received"  # claim received, processing
    under_review = "under_review"  # adjuster looking at it
    approved = "approved"  # claim approved with payout
    needs_more_info = "needs_more_info"  # adjuster needs more evidence
    rejected = "rejected"  # claim rejected
    paid = "paid"  # payment sent


_LANG_DETECT_SYSTEM = """\
You detect the language of a short text message from a smallholder farmer.
Return JSON with the ISO 639-1 language code and a confidence score.
If the input is empty or unintelligible, default to 'en' with low confidence.
"""


def detect_language(text: str) -> tuple[str, float]:
    """Return (iso_code, confidence). Falls back to ('en', 0.5) on parse error."""
    if not text or not text.strip():
        return "en", 0.5

    raw = text_chat(
        system=_LANG_DETECT_SYSTEM,
        user_text=(
            f"Text: {text!r}\n\n"
            'Return EXACTLY: {"language":"<iso639-1>","confidence":<0.0-1.0>}'
        ),
        json_mode=True,
        max_tokens=60,
        temperature=0.0,
    )
    try:
        data = json.loads(raw)
        code = str(data.get("language", "en")).lower()[:2]
        conf = float(data.get("confidence", 0.5))
        if code not in SUPPORTED_LANGUAGES:
            code = "en"
        return code, conf
    except (json.JSONDecodeError, ValueError, TypeError):
        return "en", 0.5


_LOCALIZE_SYSTEM = """\
You write short, warm, plainspoken messages to a smallholder farmer
about their crop insurance claim. Use the target language. Keep messages
under 280 characters. Do not invent facts beyond what's provided.
Do not use markdown or emoji.
"""


def localize(message_en: str, *, target_language: str) -> str:
    """Translate (or rewrite) an English message into the target language."""
    if target_language == "en":
        return message_en
    lang_name = SUPPORTED_LANGUAGES.get(target_language, "English")
    return text_chat(
        system=_LOCALIZE_SYSTEM,
        user_text=(
            f"Translate this message into {lang_name}. "
            f"Preserve the meaning. Return ONLY the translated text, no quotes.\n\n"
            f"Message:\n{message_en}"
        ),
        max_tokens=300,
        temperature=0.2,
    ).strip()


def _english_template(kind: FarmerMessageKind, claim: Claim) -> str:
    name = claim.farmer.name.split()[0] if claim.farmer.name else "there"
    crop = claim.damage.crop_type
    cf_id = claim.claim_id

    if kind is FarmerMessageKind.received:
        return (
            f"Hi {name}, we received your claim for {crop} damage. "
            f"Reference {cf_id}. We will review it and get back to you shortly."
        )
    if kind is FarmerMessageKind.under_review:
        return (
            f"Hi {name}, an adjuster is reviewing your {crop} claim ({cf_id}). "
            f"No action needed from you right now."
        )
    if kind is FarmerMessageKind.approved:
        payout = f"${claim.estimated_loss_usd:.2f}"
        return (
            f"Good news, {name}. Your claim {cf_id} for {crop} damage was approved. "
            f"Estimated payout {payout}. We will notify you when payment is sent."
        )
    if kind is FarmerMessageKind.needs_more_info:
        return (
            f"Hi {name}, the adjuster needs more information on claim {cf_id}. "
            f"Please send any additional photos or a short voice note describing "
            f"what happened to your {crop}."
        )
    if kind is FarmerMessageKind.rejected:
        return (
            f"Hi {name}, after review we were unable to approve claim {cf_id}. "
            f"Reply STATUS to hear more, or APPEAL to ask for a second look."
        )
    if kind is FarmerMessageKind.paid:
        return (
            f"Hi {name}, payment for claim {cf_id} has been released. "
            f"Please allow a few days for it to arrive in your account."
        )
    raise ValueError(f"unknown message kind: {kind}")


def status_message(claim: Claim, *, target_language: str | None = None) -> str:
    """Localized farmer-facing message reflecting the claim's current status."""
    language = target_language or claim.farmer.language or "en"
    kind_map = {
        ClaimStatus.pending_review: FarmerMessageKind.received,
        ClaimStatus.approved: FarmerMessageKind.approved,
        ClaimStatus.rejected: FarmerMessageKind.rejected,
        ClaimStatus.submitted: FarmerMessageKind.under_review,
        ClaimStatus.paid: FarmerMessageKind.paid,
    }
    kind = kind_map.get(claim.status, FarmerMessageKind.received)
    english = _english_template(kind, claim)
    return localize(english, target_language=language)
