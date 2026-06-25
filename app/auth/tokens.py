"""Opaque-token session + one-time-token helpers.

We don't ship a full JWT implementation here on purpose:
- Sessions are tracked in SQLite. Logging out is a single delete.
- One-time tokens (email verification, password reset) are also stored
  with explicit expiry so they can be invalidated server-side.

Both shapes are short random URL-safe strings; the security model is
that the token IS the secret. Lookups are constant-time-ish via SQLite
parameterised queries.
"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta

from sqlmodel import Field, Session, SQLModel, select

from app.storage.db import get_engine

ACCESS_TTL = timedelta(hours=1)
REFRESH_TTL = timedelta(days=30)
EMAIL_VERIFICATION_TTL = timedelta(hours=24)
PASSWORD_RESET_TTL = timedelta(hours=1)


class SessionRow(SQLModel, table=True):
    __tablename__ = "auth_sessions"

    token: str = Field(primary_key=True)
    user_id: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    refresh_until: datetime
    user_agent: str = ""
    ip: str = ""


class OneTimeTokenRow(SQLModel, table=True):
    __tablename__ = "auth_one_time_tokens"

    token: str = Field(primary_key=True)
    user_id: str = Field(index=True)
    purpose: str = Field(description="email_verification | password_reset")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    consumed_at: datetime | None = None


def _now() -> datetime:
    return datetime.utcnow()


def _new_token(prefix: str) -> str:
    return f"{prefix}_{secrets.token_urlsafe(32)}"


def create_session(user_id: str, *, user_agent: str = "", ip: str = "") -> str:
    SQLModel.metadata.create_all(get_engine())
    token = _new_token("sess")
    row = SessionRow(
        token=token,
        user_id=user_id,
        refresh_until=_now() + REFRESH_TTL,
        user_agent=user_agent[:255],
        ip=ip[:64],
    )
    with Session(get_engine()) as s:
        s.add(row)
        s.commit()
    return token


def get_session_user(token: str) -> str | None:
    if not token:
        return None
    with Session(get_engine()) as s:
        row = s.get(SessionRow, token)
        if row is None or row.refresh_until < _now():
            return None
        return row.user_id


def delete_session(token: str) -> None:
    with Session(get_engine()) as s:
        row = s.get(SessionRow, token)
        if row is not None:
            s.delete(row)
            s.commit()


def issue_email_verification_token(user_id: str) -> str:
    return _issue_one_time(user_id, "email_verification", EMAIL_VERIFICATION_TTL)


def issue_password_reset_token(user_id: str) -> str:
    return _issue_one_time(user_id, "password_reset", PASSWORD_RESET_TTL)


def _issue_one_time(user_id: str, purpose: str, ttl: timedelta) -> str:
    SQLModel.metadata.create_all(get_engine())
    token = _new_token(purpose[:4])
    row = OneTimeTokenRow(
        token=token,
        user_id=user_id,
        purpose=purpose,
        expires_at=_now() + ttl,
    )
    with Session(get_engine()) as s:
        s.add(row)
        s.commit()
    return token


def redeem_email_verification_token(token: str) -> str | None:
    return _redeem(token, "email_verification")


def redeem_password_reset_token(token: str) -> str | None:
    return _redeem(token, "password_reset")


def _redeem(token: str, purpose: str) -> str | None:
    with Session(get_engine()) as s:
        row = s.get(OneTimeTokenRow, token)
        if row is None or row.purpose != purpose:
            return None
        if row.consumed_at is not None:
            return None
        if row.expires_at < _now():
            return None
        row.consumed_at = _now()
        s.add(row)
        s.commit()
        return row.user_id
