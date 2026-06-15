"""SQLite engine + schema for claim persistence.

Claims are stored as JSON in a single column for flexibility; a few hot
columns (status, farmer_phone, created_at) are duplicated for indexing.
"""

from __future__ import annotations

from datetime import datetime
from functools import lru_cache

from sqlmodel import Field, SQLModel, create_engine

from app.config import get_settings


class ClaimRow(SQLModel, table=True):
    __tablename__ = "claims"

    claim_id: str = Field(primary_key=True)
    status: str = Field(index=True)
    created_at: datetime = Field(index=True)
    farmer_phone: str = Field(index=True)
    farmer_name: str
    farmer_language: str = Field(default="en")
    crop_type: str
    estimated_loss_usd: float
    pdf_path: str | None = None
    insurer_claim_id: str | None = None
    payload: str  # full Claim JSON


@lru_cache
def get_engine():
    s = get_settings()
    url = s.database_url
    # SQLModel needs check_same_thread off for SQLite in Streamlit's threaded runtime.
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    engine = create_engine(url, connect_args=connect_args)
    SQLModel.metadata.create_all(engine)
    return engine
