"""Telegram Bot API client.

Telegram has no trial restrictions, no 24-hour window, and no message
templates — its Bot API works the same on day one as on day 1000. This
makes it the most reliable demo channel for ClaimFarm.

Reference: https://core.telegram.org/bots/api
"""

from __future__ import annotations

import logging

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


def _api(method: str) -> str:
    s = get_settings()
    if not s.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN must be set")
    return f"{s.telegram_api_base.rstrip('/')}/bot{s.telegram_bot_token}/{method}"


def send_message(chat_id: int | str, text: str) -> dict:
    """Send a plain-text message to a Telegram chat."""
    r = httpx.post(
        _api("sendMessage"),
        json={"chat_id": chat_id, "text": text},
        timeout=15.0,
    )
    if r.status_code >= 400:
        logger.warning("telegram sendMessage failed: %s %s", r.status_code, r.text[:300])
    r.raise_for_status()
    return r.json()


def set_webhook(url: str) -> dict:
    """Register the inbound webhook with Telegram."""
    r = httpx.post(_api("setWebhook"), json={"url": url}, timeout=15.0)
    r.raise_for_status()
    return r.json()


def delete_webhook() -> dict:
    r = httpx.post(_api("deleteWebhook"), timeout=15.0)
    r.raise_for_status()
    return r.json()


def get_file_info(file_id: str) -> dict:
    """Resolve a file_id from a message to file_path + size metadata."""
    r = httpx.get(_api("getFile"), params={"file_id": file_id}, timeout=15.0)
    r.raise_for_status()
    return r.json()


def download_file(file_id: str) -> tuple[bytes, str]:
    """Resolve + download a Telegram file. Returns (bytes, mime-best-guess)."""
    s = get_settings()
    info = get_file_info(file_id)
    file_path = info["result"]["file_path"]
    download_url = (
        f"{s.telegram_api_base.rstrip('/')}/file/bot{s.telegram_bot_token}/{file_path}"
    )
    r = httpx.get(download_url, timeout=30.0, follow_redirects=True)
    r.raise_for_status()
    # Telegram returns the raw file. Guess MIME from extension.
    ext = file_path.lower().rsplit(".", 1)[-1] if "." in file_path else "jpeg"
    mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}.get(ext, "image/jpeg")
    return r.content, mime
