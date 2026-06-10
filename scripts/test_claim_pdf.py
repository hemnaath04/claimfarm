"""End-to-end smoke test: photo + GPS + date -> rendered PDF claim.

Usage:
    uv run python scripts/test_claim_pdf.py <image_path_or_url> <lat> <lon> <YYYY-MM-DD>
"""

from __future__ import annotations

import sys
from datetime import date

from dotenv import load_dotenv

load_dotenv()

from app.agents.claim_drafter import build_claim, render_claim_pdf
from app.agents.damage_assessor import assess_damage
from app.agents.weather_corroborator import corroborate
from app.models.claim import Farmer


def main() -> int:
    if len(sys.argv) < 5:
        print(
            "usage: test_claim_pdf.py <image_path_or_url> <lat> <lon> <YYYY-MM-DD>",
            file=sys.stderr,
        )
        return 2

    image, lat_s, lon_s, date_s = sys.argv[1:5]
    lat, lon = float(lat_s), float(lon_s)
    claim_date = date.fromisoformat(date_s)

    damage = assess_damage(image)
    weather, corr = corroborate(damage, latitude=lat, longitude=lon, claim_date=claim_date)

    farmer = Farmer(
        name="Demo Farmer",
        phone="+1-555-0100",
        language="en",
        latitude=lat,
        longitude=lon,
        region="Test region",
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

    out = render_claim_pdf(claim, f"data/pdfs/{claim.claim_id}.pdf")
    print(f"Claim {claim.claim_id} written to {out}")
    print(f"Estimated loss: ${claim.estimated_loss_usd:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
