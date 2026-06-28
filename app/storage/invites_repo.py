"""SQLModel-backed invite store for invite-only admin access.

Invites are issued by an owner and redeemed once by an invitee to set their
password. Each row carries an unguessable token (the secret), a target role,
and an explicit expiry so stale invites stop working server-side.
"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta
from uuid import uuid4

from sqlmodel import Field, Session, SQLModel, select

from app.models.user import UserRole
from app.storage.db import get_engine


class InviteRow(SQLModel, table=True):
    __tablename__ = "invites"

    invite_id: str = Field(primary_key=True)
    token: str = Field(index=True, unique=True)
    email: str = ""
    role: str = Field(default=UserRole.reviewer.value)
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    used_at: datetime | None = None
    used_by_user_id: str | None = None


def _ensure_table() -> None:
    SQLModel.metadata.create_all(get_engine())


def _now() -> datetime:
    return datetime.utcnow()


def create(email: str, role: str, created_by: str, ttl_days: int = 7) -> InviteRow:
    _ensure_table()
    row = InviteRow(
        invite_id=f"inv_{uuid4().hex[:12]}",
        token=secrets.token_urlsafe(24),
        email=(email or "").lower(),
        role=role,
        created_by=created_by,
        expires_at=_now() + timedelta(days=ttl_days),
    )
    with Session(get_engine(), expire_on_commit=False) as s:
        s.add(row)
        s.commit()
        return row


def get_by_token(token: str) -> InviteRow | None:
    if not token:
        return None
    _ensure_table()
    with Session(get_engine(), expire_on_commit=False) as s:
        return s.exec(select(InviteRow).where(InviteRow.token == token)).first()


def list_all() -> list[InviteRow]:
    _ensure_table()
    with Session(get_engine(), expire_on_commit=False) as s:
        return list(s.exec(select(InviteRow).order_by(InviteRow.created_at.desc())).all())


def mark_used(token: str, user_id: str) -> InviteRow | None:
    _ensure_table()
    with Session(get_engine(), expire_on_commit=False) as s:
        row = s.exec(select(InviteRow).where(InviteRow.token == token)).first()
        if row is None:
            return None
        row.used_at = _now()
        row.used_by_user_id = user_id
        s.add(row)
        s.commit()
        return row


def revoke(invite_id: str) -> bool:
    _ensure_table()
    with Session(get_engine(), expire_on_commit=False) as s:
        row = s.get(InviteRow, invite_id)
        if row is None:
            return False
        s.delete(row)
        s.commit()
        return True


def is_valid(row: InviteRow) -> bool:
    """An invite is usable while it is unconsumed and not past its expiry."""
    return row.used_at is None and _now() < row.expires_at
