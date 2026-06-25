"""SQLModel-backed user store."""

from __future__ import annotations

from datetime import datetime
from typing import Iterable

from sqlmodel import Field, Session, SQLModel, select

from app.models.user import IdentityStatus, UserRole
from app.storage.db import get_engine


class UserRow(SQLModel, table=True):
    __tablename__ = "users"

    user_id: str = Field(primary_key=True)
    email: str = Field(index=True, unique=True)
    name: str = ""
    org_id: str | None = Field(default=None, index=True)
    role: str = Field(default=UserRole.reviewer.value)
    password_hash: str | None = None
    email_verified: bool = False
    phone: str | None = None
    locale: str = "en"
    identity_status: str = Field(default=IdentityStatus.not_started.value)
    identity_score: float | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_seen_at: datetime | None = None
    disabled: bool = False


def _ensure_table() -> None:
    SQLModel.metadata.create_all(get_engine())


def get(user_id: str) -> UserRow | None:
    _ensure_table()
    with Session(get_engine()) as s:
        return s.get(UserRow, user_id)


def get_by_email(email: str) -> UserRow | None:
    _ensure_table()
    with Session(get_engine()) as s:
        return s.exec(select(UserRow).where(UserRow.email == email.lower())).first()


def upsert(row: UserRow) -> UserRow:
    _ensure_table()
    row.email = row.email.lower()
    with Session(get_engine()) as s:
        existing = s.get(UserRow, row.user_id)
        if existing:
            for k, v in row.model_dump().items():
                setattr(existing, k, v)
            s.add(existing)
            s.commit()
            return existing
        s.add(row)
        s.commit()
        return row


def update_last_seen(user_id: str) -> None:
    _ensure_table()
    with Session(get_engine()) as s:
        u = s.get(UserRow, user_id)
        if u is None:
            return
        u.last_seen_at = datetime.utcnow()
        s.add(u)
        s.commit()


def list_all() -> Iterable[UserRow]:
    _ensure_table()
    with Session(get_engine()) as s:
        return list(s.exec(select(UserRow)).all())
