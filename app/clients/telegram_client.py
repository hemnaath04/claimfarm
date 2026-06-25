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


def send_message(
    chat_id: int | str,
    text: str,
    *,
    reply_markup: dict | None = None,
) -> dict:
    """Send a plain-text message to a Telegram chat."""
    payload: dict = {"chat_id": chat_id, "text": text}
    if reply_markup is not None:
        payload["reply_markup"] = reply_markup
    r = httpx.post(_api("sendMessage"), json=payload, timeout=15.0)
    if r.status_code >= 400:
        logger.warning("telegram sendMessage failed: %s %s", r.status_code, r.text[:300])
    r.raise_for_status()
    return r.json()


def location_request_keyboard(button_text: str = "📍 Share my farm location") -> dict:
    """A one-tap keyboard that asks Telegram to send the user's location.

    Telegram delivers the location as a regular update with `message.location`
    populated. After the tap, the keyboard is hidden again.
    """
    return {
        "keyboard": [[{"text": button_text, "request_location": True}]],
        "resize_keyboard": True,
        "one_time_keyboard": True,
    }


def remove_keyboard() -> dict:
    return {"remove_keyboard": True}


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
