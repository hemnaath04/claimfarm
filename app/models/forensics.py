"""Schemas for photo forensics + authenticity verification."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class PhotoForensics(BaseModel):
    """Everything we can learn about an inbound photo *besides* its content."""

    # EXIF
    has_exif: bool = Field(description="True when the image carried any EXIF metadata")
    capture_time: datetime | None = Field(default=None, description="EXIF DateTimeOriginal")
    gps_lat: float | None = None
    gps_lon: float | None = None
    camera_make: str | None = None
    camera_model: str | None = None
    software: str | None = Field(
        default=None,
        description="EXIF Software field — sometimes flags edits ('Photoshop', 'Snapseed')",
    )

    # Raw image
    width: int | None = None
    height: int | None = None
    file_size_bytes: int

    # Authenticity verdict (from Qwen-VL)
    appears_real_phone_photo: bool = Field(
        default=True,
        description="False if Qwen-VL thinks the image is a screenshot, render, or AI generation",
    )
    authenticity_score: float = Field(
        default=1.0, ge=0.0, le=1.0, description="0 = likely fake, 1 = likely real phone photo"
    )
    authenticity_reasoning: str = ""

    # Aggregated flags surfaced on the adjuster dashboard
    flags: list[str] = Field(default_factory=list)
