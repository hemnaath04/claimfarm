"""Smoke test for language detection + localized status messages.

Usage:
    uv run python scripts/test_multilingual.py
"""

from __future__ import annotations

from datetime import date

from dotenv import load_dotenv

load_dotenv()

from app.agents.multilingual import (
    SUPPORTED_LANGUAGES,
    detect_language,
    localize,
    status_message,
)
from app.models.claim import Claim, ClaimStatus, Farmer
from app.models.damage import DamageAssessment, DamageCause
from app.models.weather import CorroborationResult, WeatherSummary


def _fake_claim(language: str, name: str) -> Claim:
    return Claim(
        farmer=Farmer(
            name=name,
            phone="+91-555-0100",
            language=language,
            latitude=20.5937,
            longitude=78.9629,
            region="Demo region",
            farm_area_hectares=1.2,
        ),
        crop_type="rice",
        date_of_damage=date(2026, 6, 1),
        damage=DamageAssessment(
            crop_type="rice",
            damage_cause=DamageCause.flood,
            severity=85,
            affected_area_pct=95,
            confidence=0.93,
            visible_indicators=["standing water", "submerged paddy"],
            notes="Field appears flooded across most of the visible area.",
        ),
        weather=WeatherSummary(
            latitude=20.5937,
            longitude=78.9629,
            start_date=date(2026, 5, 2),
            end_date=date(2026, 6, 1),
            total_precip_mm=480.0,
            max_temp_c=34.2,
            min_temp_c=22.0,
            max_wind_kmh=42.0,
            days_above_35c=0,
            days_with_heavy_rain=6,
            days_with_frost=0,
            consecutive_dry_days=0,
        ),
        corroboration=CorroborationResult(
            corroborated=True,
            strength=0.92,
            evidence="Six heavy-rain days in window match the visible flooding.",
        ),
        estimated_loss_usd=920.0,
        status=ClaimStatus.approved,
    )


def main() -> int:
    print("=== Language detection ===")
    samples = {
        "en": "My rice field is completely flooded after the storm",
        "hi": "मेरी धान की फसल बाढ़ से बर्बाद हो गई है",
        "es": "Mi cosecha de maíz se perdió por la sequía",
        "sw": "Shamba langu la mahindi limeharibika kwa ukame",
    }
    for expected, text in samples.items():
        code, conf = detect_language(text)
        print(f"  expected={expected}  got={code} (conf={conf:.2f})  text={text!r}")

    print("\n=== Localized approval messages ===")
    for code in ["en", "hi", "es", "sw", "pt"]:
        if code not in SUPPORTED_LANGUAGES:
            continue
        msg = status_message(_fake_claim(code, "Ravi Kumar"))
        print(f"\n  [{code}] {msg}")

    print("\n=== Direct localize() smoke test ===")
    base = "An adjuster is reviewing your claim. We will reach out within 48 hours."
    print(f"  EN: {base}")
    print(f"  HI: {localize(base, target_language='hi')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
