"""CRUD repository for FarmerProfile objects backed by SQLite.

Profiles are keyed by `chat_id` (the messaging-channel identity) for the
common upsert path, with `farmer_id` as the stable primary key. The bot
registration flow reads/writes these incrementally via `get_or_create` and
`update`; the admin dashboard lists them via `list_all`.
"""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlmodel import Field, Session, SQLModel, select

from app.storage.db import get_engine


class FarmerProfileRow(SQLModel, table=True):
    __tablename__ = "farmer_profiles"

    farmer_id: str = Field(
        default_factory=lambda: f"frm_{uuid4().hex[:12]}", primary_key=True
    )
    channel: str = Field(default="telegram")
    chat_id: str = Field(index=True, unique=True)
    name: str = ""
    language: str = Field(default="en")
    phone: str = ""
    region: str = ""
    village: str = ""
    crops: str = ""  # comma-separated
    farm_area_hectares: float = 0.0
    email: str = ""
    latitude: float | None = None
    longitude: float | None = None
    registration_step: str = Field(default="new")
    registration_complete: bool = Field(default=False)
    # When set, the next email-shaped inbound message should be saved as the
    # farmer's email and used to mail the PDF for this claim (Phase 4 fallback
    # when no email is on file at the time the farmer taps "email me a copy").
    pending_pdf_claim_id: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


def get_by_chat_id(chat_id: str) -> FarmerProfileRow | None:
    with Session(get_engine()) as session:
        stmt = select(FarmerProfileRow).where(FarmerProfileRow.chat_id == chat_id)
        return session.exec(stmt).first()


def upsert(row: FarmerProfileRow) -> FarmerProfileRow:
    """Insert a new profile or update the existing one matching `chat_id`."""
    with Session(get_engine(), expire_on_commit=False) as session:
        stmt = select(FarmerProfileRow).where(
            FarmerProfileRow.chat_id == row.chat_id
        )
        existing = session.exec(stmt).first()
        if existing:
            data = row.model_dump(exclude={"farmer_id", "created_at"})
            for key, value in data.items():
                setattr(existing, key, value)
            existing.updated_at = datetime.utcnow()
            session.add(existing)
            session.commit()
            return existing
        session.add(row)
        session.commit()
        return row


def update(chat_id: str, **fields) -> FarmerProfileRow | None:
    with Session(get_engine(), expire_on_commit=False) as session:
        stmt = select(FarmerProfileRow).where(
            FarmerProfileRow.chat_id == chat_id
        )
        row = session.exec(stmt).first()
        if row is None:
            return None
        for key, value in fields.items():
            if hasattr(row, key):
                setattr(row, key, value)
        row.updated_at = datetime.utcnow()
        if row.registration_step == "complete":
            row.registration_complete = True
        session.add(row)
        session.commit()
        return row


def get_or_create(chat_id: str, **defaults) -> FarmerProfileRow:
    existing = get_by_chat_id(chat_id)
    if existing is not None:
        return existing
    row = FarmerProfileRow(chat_id=chat_id, **defaults)
    return upsert(row)


def set_pending_pdf(chat_id: str, claim_id: str | None) -> FarmerProfileRow | None:
    """Record (or clear with ``None``) the claim whose PDF should be emailed
    once the farmer supplies an address."""
    return update(chat_id, pending_pdf_claim_id=claim_id)


def list_all() -> list[FarmerProfileRow]:
    with Session(get_engine()) as session:
        stmt = select(FarmerProfileRow).order_by(
            FarmerProfileRow.created_at.desc()
        )
        return list(session.exec(stmt).all())
