"""Tiny persistent store mapping a Telegram chat_id to a farmer's saved
GPS location. Backed by a JSON file under /tmp so it survives uvicorn
reloads but is trivial to inspect and reset for demos.

In production this would live in the same SQLite (or Tablestore) that
backs Claims; for hackathon scope a flat file is fine.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path

_LOCK = threading.Lock()
_PATH = Path("/tmp/claimfarm_farmer_profiles.json")


def _load() -> dict[str, dict]:
    if not _PATH.exists():
        return {}
    try:
        return json.loads(_PATH.read_text())
    except Exception:
        return {}


def _save(data: dict[str, dict]) -> None:
    _PATH.parent.mkdir(parents=True, exist_ok=True)
    _PATH.write_text(json.dumps(data, indent=2))


def set_location(chat_id: int, latitude: float, longitude: float, name: str = "") -> None:
    with _LOCK:
        data = _load()
        data[str(chat_id)] = {
            "lat": float(latitude),
            "lon": float(longitude),
            "name": name,
        }
        _save(data)


def get_location(chat_id: int) -> tuple[float, float] | None:
    with _LOCK:
        data = _load()
    rec = data.get(str(chat_id))
    if not rec:
        return None
    try:
        return float(rec["lat"]), float(rec["lon"])
    except (KeyError, ValueError, TypeError):
        return None


def get_name(chat_id: int) -> str | None:
    with _LOCK:
        data = _load()
    rec = data.get(str(chat_id))
    if not rec:
        return None
    return rec.get("name") or None
