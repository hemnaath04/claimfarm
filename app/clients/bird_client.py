"""Bird (formerly MessageBird) Conversations API client.

Alternative to Twilio for WhatsApp inbound/outbound. Trial accounts on
Bird have looser sandbox restrictions than Twilio for cross-account
media access and freeform replies within the 24-hour conversation
window, which is what we need.

Endpoints used here are best-effort against the current Bird Channels
API. Adjusted at runtime against the actual payload Bird sends to
our webhook (logged on first inbound).
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


def _auth_headers() -> dict[str, str]:
    s = get_settings()
    if not s.bird_api_key:
        raise RuntimeError("BIRD_API_KEY must be set")
    return {
        "Authorization": f"AccessKey {s.bird_api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _messages_url() -> str:
    s = get_settings()
    if not (s.bird_workspace_id and s.bird_channel_id):
        raise RuntimeError("BIRD_WORKSPACE_ID and BIRD_CHANNEL_ID must be set")
    return (
        f"{s.bird_base_url.rstrip('/')}/workspaces/{s.bird_workspace_id}"
        f"/channels/{s.bird_channel_id}/messages"
    )


def send_whatsapp(to_phone: str, body: str) -> dict:
    """Send a freeform WhatsApp text via Bird Conversations API.

    `to_phone` should be an E.164 phone number (e.g. +18573796762).
    """
    payload: dict[str, Any] = {
        "receiver": {
            "contacts": [
                {"identifierKey": "phonenumber", "identifierValue": to_phone}
            ]
        },
        "body": {"type": "text", "text": {"text": body}},
    }
    r = httpx.post(_messages_url(), headers=_auth_headers(), json=payload, timeout=20.0)
    if r.status_code >= 400:
        logger.warning("bird send_whatsapp failed: %s %s", r.status_code, r.text[:300])
    r.raise_for_status()
    return r.json()


def download_media(media_url: str) -> bytes:
    """Fetch a Bird-hosted media URL. Bird typically requires the same
    AccessKey auth on its media endpoints."""
    headers = {"Authorization": f"AccessKey {get_settings().bird_api_key}"}
    r = httpx.get(media_url, headers=headers, timeout=30.0, follow_redirects=True)
    r.raise_for_status()
    return r.content
