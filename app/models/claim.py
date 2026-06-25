from datetime import date, datetime
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field

from app.models.damage import DamageAssessment
from app.models.forensics import PhotoForensics
from app.models.weather import CorroborationResult, WeatherSummary


class ClaimStatus(str, Enum):
    pending_review = "pending_review"
    approved = "approved"
    rejected = "rejected"
    submitted = "submitted"
    paid = "paid"


class Farmer(BaseModel):
    name: str
    phone: str
    language: str = Field(default="en", description="ISO 639-1 code, e.g. 'en', 'hi', 'sw'")
    latitude: float
    longitude: float
    region: str = Field(default="", description="Free-text region or admin area")
    farm_area_hectares: float


class Claim(BaseModel):
    claim_id: str = Field(default_factory=lambda: f"CF-{uuid4().hex[:10].upper()}")
    farmer: Farmer
    crop_type: str
    date_of_damage: date
    photo_urls: list[str] = Field(default_factory=list)
    farmer_narrative: str = Field(default="", description="What the farmer wrote/said")
    damage: DamageAssessment
    weather: WeatherSummary
    corroboration: CorroborationResult
    forensics: PhotoForensics | None = None
    estimated_loss_usd: float = Field(ge=0.0)
    status: ClaimStatus = ClaimStatus.pending_review
    created_at: datetime = Field(default_factory=datetime.utcnow)
    adjuster_notes: str = ""
