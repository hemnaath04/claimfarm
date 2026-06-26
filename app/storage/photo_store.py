"""Local photo persistence for claims.

FC 3.0 / Singapore has writable /tmp, so for the demo we use a stable
on-disk path (``data/photos/{claim_id}.{ext}``) and serve it through the
backend. Production would swap to Alibaba OSS — same interface, swap
``save_bytes`` to call ``alibaba_oss.upload_bytes`` and return the OSS
public URL or a signed URL.
"""

from __future__ import annotations

import logging
import mimetypes
from pathlib import Path

logger = logging.getLogger(__name__)

PHOTO_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "photos"


def _ext_from_mime(mime: str) -> str:
    if mime in ("image/jpeg", "image/jpg"):
        return ".jpg"
    if mime == "image/png":
        return ".png"
    if mime == "image/webp":
        return ".webp"
    guessed = mimetypes.guess_extension(mime)
    return guessed or ".bin"


def save_bytes(claim_id: str, data: bytes, mime: str = "image/jpeg") -> Path:
    """Write the photo to disk; return the resolved path."""
    PHOTO_DIR.mkdir(parents=True, exist_ok=True)
    ext = _ext_from_mime(mime)
    path = PHOTO_DIR / f"{claim_id}{ext}"
    try:
        path.write_bytes(data)
    except OSError:
        logger.exception("photo write failed for %s", claim_id)
    return path


def find_photo(claim_id: str) -> Path | None:
    """Return the path of the photo for this claim_id, regardless of ext."""
    if not PHOTO_DIR.exists():
        return None
    for path in PHOTO_DIR.iterdir():
        if path.stem == claim_id and path.is_file():
            return path
    return None


def public_url(claim_id: str) -> str:
    """Reference the photo via the public backend route."""
    return f"/api/claims/{claim_id}/photo"
