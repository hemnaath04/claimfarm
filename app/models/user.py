"""User + organisation models, including RBAC roles."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, EmailStr, Field


class UserRole(str, Enum):
    """RBAC roles. ORGs hierarchy: owner > admin > moderator > reviewer > farmer.

    `farmer` is the end-user submitting claims; everyone else is staff.
    """

    owner = "owner"
    admin = "admin"
    moderator = "moderator"
    reviewer = "reviewer"
    farmer = "farmer"


class IdentityStatus(str, Enum):
    not_started = "not_started"
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    manual_review = "manual_review"


class Organisation(BaseModel):
    org_id: str = Field(default_factory=lambda: f"org_{uuid4().hex[:12]}")
    name: str
    plan: str = "pilot"   # pilot | growth | enterprise
    region: str = "ap-southeast-1"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    payments_customer_id: str | None = None  # provider-agnostic external customer id


class User(BaseModel):
    user_id: str = Field(default_factory=lambda: f"usr_{uuid4().hex[:12]}")
    email: EmailStr
    name: str = ""
    org_id: str | None = None
    role: UserRole = UserRole.reviewer
    password_hash: str | None = None
    email_verified: bool = False
    phone: str | None = None
    locale: str = "en"
    identity_status: IdentityStatus = IdentityStatus.not_started
    identity_score: float | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_seen_at: datetime | None = None
    disabled: bool = False
