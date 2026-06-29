"""Claim photo persistence.

Photos are stored as bytes in the database (the same SQLite locally / Neon
Postgres in prod that backs claims). FC's container app dir isn't writable for
the runtime user and /tmp is per-instance, so disk storage lost photos on every
instance roll — the DB keeps them durable and reachable from any instance.
Production at higher volume would swap to Alibaba OSS behind this same
interface (save_bytes / read_bytes / public_url).
"""

from __future__ import annotations

import logging

from sqlmodel import Session

from app.storage.db import PhotoRow, get_engine

logger = logging.getLogger(__name__)


def save_bytes(claim_id: str, data: bytes, mime: str = "image/jpeg") -> str:
    """Persist (or replace) the photo for a claim; return its public URL."""
    try:
        with Session(get_engine()) as s:
            row = s.get(PhotoRow, claim_id)
            if row is None:
                row = PhotoRow(claim_id=claim_id, mime=mime, data=data)
            else:
                row.mime = mime
                row.data = data
            s.add(row)
            s.commit()
    except Exception:
        logger.exception("photo save failed for %s", claim_id)
    return public_url(claim_id)


def read_bytes(claim_id: str) -> tuple[bytes, str] | None:
    """Return (bytes, mime) for a claim's photo, or None if not stored."""
    try:
        with Session(get_engine()) as s:
            row = s.get(PhotoRow, claim_id)
            if row is None:
                return None
            return bytes(row.data), row.mime
    except Exception:
        logger.exception("photo read failed for %s", claim_id)
        return None


def public_url(claim_id: str) -> str:
    """Reference the photo via the public backend route."""
    return f"/api/claims/{claim_id}/photo"
