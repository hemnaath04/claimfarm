"""Farmer profile domain model.

A FarmerProfile is the durable identity record for someone who files claims
over a messaging channel (Telegram today). It is built up incrementally during
the bot registration flow — `registration_step` tracks where the conversation
is and `registration_complete` flips once the required fields are collected.

The link back to claims is `phone`: a claim's `farmer_phone` is
f"telegram:{chat_id}", which mirrors the profile's `phone` once registered.
"""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, Field


class FarmerProfile(BaseModel):
    farmer_id: str = Field(default_factory=lambda: f"frm_{uuid4().hex[:12]}")
    channel: str = "telegram"
    chat_id: str
    name: str = ""
    language: str = Field(default="en", description="ISO 639-1 code, e.g. 'en', 'hi', 'sw'")
    phone: str = ""
    region: str = Field(default="", description="Free-text region or admin area")
    village: str = ""
    crops: str = Field(default="", description="Comma-separated crop names")
    farm_area_hectares: float = 0.0
    email: str = ""
    latitude: float | None = None
    longitude: float | None = None
    registration_step: str = "new"
    registration_complete: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
