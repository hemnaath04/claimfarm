"""Programmatic-access API keys.

Issued from `/api/keys`. Each key is shown to the user exactly once at
creation time; the database only stores a SHA-256 of the secret. Keys
carry an `org_id` + a scope label (e.g. `claims:read`, `claims:write`)
and an optional expiry.

Bearer presentation:  `Authorization: Bearer cf_live_<32 url-safe chars>`
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime

from sqlmodel import Field, Session, SQLModel, select

from app.storage.db import get_engine


KEY_PREFIX = "cf_live_"


class ApiKeyRow(SQLModel, table=True):
    __tablename__ = "api_keys"

    key_id: str = Field(primary_key=True)
    sha256: str = Field(index=True, unique=True)
    org_id: str = Field(index=True)
    name: str = ""
    scope: str = "claims:read"
    created_by_user_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_used_at: datetime | None = None
    revoked_at: datetime | None = None
    expires_at: datetime | None = None


def _ensure_table() -> None:
    SQLModel.metadata.create_all(get_engine())


def _hash_secret(secret: str) -> str:
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


def issue(
    *,
    org_id: str,
    created_by_user_id: str,
    name: str = "",
    scope: str = "claims:read",
    expires_at: datetime | None = None,
) -> tuple[ApiKeyRow, str]:
    """Create a new API key. Returns (row, plaintext_secret). Save the
    secret immediately — it is not retrievable after this call."""
    _ensure_table()
    secret = KEY_PREFIX + secrets.token_urlsafe(32)
    row = ApiKeyRow(
        key_id=f"key_{secrets.token_urlsafe(8)}",
        sha256=_hash_secret(secret),
        org_id=org_id,
        name=name[:120],
        scope=scope,
        created_by_user_id=created_by_user_id,
        expires_at=expires_at,
    )
    with Session(get_engine(), expire_on_commit=False) as s:
        s.add(row)
        s.commit()
    return row, secret


def lookup(secret: str) -> ApiKeyRow | None:
    """Resolve a presented secret to a row. Returns None for unknown,
    revoked, or expired keys. Updates last_used_at on success."""
    if not secret or not secret.startswith(KEY_PREFIX):
        return None
    sha = _hash_secret(secret)
    with Session(get_engine()) as s:
        row = s.exec(select(ApiKeyRow).where(ApiKeyRow.sha256 == sha)).first()
        if row is None or row.revoked_at is not None:
            return None
        if row.expires_at is not None and row.expires_at < datetime.utcnow():
            return None
        row.last_used_at = datetime.utcnow()
        s.add(row)
        s.commit()
        return row


def revoke(key_id: str) -> bool:
    with Session(get_engine()) as s:
        row = s.get(ApiKeyRow, key_id)
        if row is None:
            return False
        row.revoked_at = datetime.utcnow()
        s.add(row)
        s.commit()
        return True


def list_for_org(org_id: str) -> list[ApiKeyRow]:
    _ensure_table()
    with Session(get_engine()) as s:
        return list(s.exec(select(ApiKeyRow).where(ApiKeyRow.org_id == org_id)).all())
