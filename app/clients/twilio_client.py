"""Twilio WhatsApp client: outbound messages + inbound media download."""

from __future__ import annotations

from functools import lru_cache

import httpx
from twilio.rest import Client

from app.config import get_settings


@lru_cache
def _client() -> Client:
    s = get_settings()
    if not (s.twilio_account_sid and s.twilio_auth_token):
        raise RuntimeError(
            "TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN must be set"
        )
    return Client(s.twilio_account_sid, s.twilio_auth_token)


def _normalize(num: str) -> str:
    """Ensure the WhatsApp prefix is present."""
    return num if num.startswith("whatsapp:") else f"whatsapp:{num}"


def send_whatsapp(to: str, body: str) -> dict:
    """Send a plain-text WhatsApp message. Returns Twilio sid + status."""
    s = get_settings()
    msg = _client().messages.create(
        from_=_normalize(s.twilio_whatsapp_from),
        to=_normalize(to),
        body=body,
    )
    return {"sid": msg.sid, "status": msg.status}


def download_media(media_url: str) -> bytes:
    """Fetch a Twilio-hosted media URL using account credentials."""
    s = get_settings()
    r = httpx.get(
        media_url,
        auth=(s.twilio_account_sid, s.twilio_auth_token),
        timeout=30.0,
        follow_redirects=True,
    )
    r.raise_for_status()
    return r.content
