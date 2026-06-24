"""Alibaba Cloud Object Storage Service (OSS) client.

Used to persist farmer-submitted photos and generated claim PDFs in
production. This file also serves as the "proof of Alibaba Cloud
deployment" code reference required by the hackathon rules
(referenced from docs/alibaba-cloud-proof.md).
"""

from __future__ import annotations

import mimetypes
from functools import lru_cache
from pathlib import Path

import oss2  # type: ignore

from app.config import get_settings


@lru_cache
def _bucket() -> oss2.Bucket:
    s = get_settings()
    if not (s.alibaba_access_key_id and s.alibaba_access_key_secret):
        raise RuntimeError(
            "ALIBABA_ACCESS_KEY_ID and ALIBABA_ACCESS_KEY_SECRET must be set"
        )
    auth = oss2.Auth(s.alibaba_access_key_id, s.alibaba_access_key_secret)
    return oss2.Bucket(auth, s.oss_endpoint, s.oss_bucket)


def upload_bytes(key: str, data: bytes, *, content_type: str | None = None) -> str:
    """Upload raw bytes to OSS. Returns the public URL of the object."""
    headers = {"Content-Type": content_type} if content_type else None
    _bucket().put_object(key, data, headers=headers)
    return public_url(key)


def upload_file(key: str, local_path: str | Path) -> str:
    """Upload a local file. Content-Type is guessed from extension."""
    path = Path(local_path)
    ctype, _ = mimetypes.guess_type(str(path))
    return upload_bytes(key, path.read_bytes(), content_type=ctype)


def download(key: str) -> bytes:
    return _bucket().get_object(key).read()


def public_url(key: str) -> str:
    s = get_settings()
    # Strip protocol from endpoint, then re-prefix with bucket subdomain
    host = s.oss_endpoint.replace("https://", "").replace("http://", "")
    return f"https://{s.oss_bucket}.{host}/{key}"


def signed_url(key: str, *, expires_seconds: int = 3600) -> str:
    """Pre-signed URL for private objects."""
    return _bucket().sign_url("GET", key, expires_seconds)


def exists(key: str) -> bool:
    return _bucket().object_exists(key)
