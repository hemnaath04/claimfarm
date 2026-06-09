from enum import Enum

from pydantic import BaseModel, Field


class DamageCause(str, Enum):
    flood = "flood"
    drought = "drought"
    hail = "hail"
    wind = "wind"
    fire = "fire"
    frost = "frost"
    pest = "pest"
    disease = "disease"
    other = "other"
    unknown = "unknown"


class DamageAssessment(BaseModel):
    crop_type: str = Field(description="Best-guess crop identification, e.g. 'rice', 'wheat', 'maize'")
    damage_cause: DamageCause = Field(description="Primary cause of the visible damage")
    severity: int = Field(ge=0, le=100, description="Overall damage severity, 0 = none, 100 = total loss")
    affected_area_pct: int = Field(ge=0, le=100, description="Percent of visible field that is damaged")
    confidence: float = Field(ge=0.0, le=1.0, description="Assessor confidence in this verdict")
    visible_indicators: list[str] = Field(
        default_factory=list,
        description="Concrete visual evidence the model used (e.g. 'yellowing leaves', 'standing water')",
    )
    notes: str = Field(default="", description="One-line summary in plain English")
