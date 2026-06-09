from datetime import date

from pydantic import BaseModel, Field


class WeatherSummary(BaseModel):
    """Aggregated weather signals over the lookback window."""

    latitude: float
    longitude: float
    start_date: date
    end_date: date
    total_precip_mm: float
    max_temp_c: float
    min_temp_c: float
    max_wind_kmh: float
    days_above_35c: int
    days_with_heavy_rain: int = Field(description="Count of days with precip_sum > 30mm")
    days_with_frost: int = Field(description="Count of days with min temp < 0°C")
    consecutive_dry_days: int = Field(description="Longest run of days with precip < 1mm")


class CorroborationResult(BaseModel):
    """LLM-judged consistency between visible damage and recent weather."""

    corroborated: bool = Field(description="True if weather plausibly caused the visible damage")
    strength: float = Field(ge=0.0, le=1.0, description="Confidence the weather supports the verdict")
    evidence: str = Field(description="One-line summary connecting weather to damage")
    flags: list[str] = Field(default_factory=list, description="Inconsistencies worth a human review")
