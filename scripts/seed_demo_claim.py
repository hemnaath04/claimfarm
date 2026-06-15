"""Run the full pipeline on a sample photo and persist the resulting claim.

Useful for populating the dashboard with realistic data before a demo.

Usage:
    uv run python scripts/seed_demo_claim.py
    uv run python scripts/seed_demo_claim.py <image_path> <lat> <lon> <YYYY-MM-DD> \
        <farmer_name> <phone> <language>
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from app.agents.claim_drafter import build_claim, render_claim_pdf
from app.agents.damage_assessor import assess_damage
from app.agents.weather_corroborator import corroborate
from app.models.claim import Farmer
from app.storage import claims_repo

DEFAULTS = (
    "data/eval/sample_drought_corn.jpg",
    "35.15",
    "-89.97",
    "2007-08-15",
    "Ravi Kumar",
    "+91-555-0100",
    "hi",
)


def main() -> int:
    args = sys.argv[1:] if len(sys.argv) > 1 else list(DEFAULTS)
    if len(args) < 7:
        print("missing args, see docstring", file=sys.stderr)
        return 2

    image, lat_s, lon_s, date_s, name, phone, language = args[:7]
    if not Path(image).exists() and not image.startswith(("http://", "https://")):
        print(f"image not found: {image}", file=sys.stderr)
        return 2

    lat, lon = float(lat_s), float(lon_s)
    claim_date = date.fromisoformat(date_s)

    print("Running damage assessor...")
    damage = assess_damage(image)
    print(f"  -> {damage.crop_type} / {damage.damage_cause.value} / sev {damage.severity}")

    print("Cross-referencing weather...")
    weather, corr = corroborate(damage, latitude=lat, longitude=lon, claim_date=claim_date)
    print(f"  -> corroborated={corr.corroborated} strength={corr.strength}")

    farmer = Farmer(
        name=name,
        phone=phone,
        language=language,
        latitude=lat,
        longitude=lon,
        region="Demo region",
        farm_area_hectares=2.5,
    )
    claim = build_claim(
        farmer=farmer,
        damage=damage,
        weather=weather,
        corroboration=corr,
        date_of_damage=claim_date,
        farmer_narrative="My field is dry, the corn never came up.",
    )

    print(f"Rendering PDF for {claim.claim_id}...")
    pdf_path = render_claim_pdf(claim, f"data/pdfs/{claim.claim_id}.pdf")
    claims_repo.save(claim, pdf_path=str(pdf_path))
    print(f"Saved {claim.claim_id} (loss ${claim.estimated_loss_usd:.2f}) to DB.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
