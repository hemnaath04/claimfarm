"""End-to-end through the mock insurer.

Spin up the insurer in another terminal first:
    uv run uvicorn mock_insurer.main:app --port 8001 --reload

Then run:
    uv run python scripts/test_insurer_flow.py <image_path_or_url> <lat> <lon> <YYYY-MM-DD>
"""

from __future__ import annotations

import json
import sys
from datetime import date

from dotenv import load_dotenv

load_dotenv()

from app.agents.claim_drafter import build_claim
from app.agents.damage_assessor import assess_damage
from app.agents.weather_corroborator import corroborate
from app.clients import insurer
from app.models.claim import Farmer


def main() -> int:
    if len(sys.argv) < 5:
        print(
            "usage: test_insurer_flow.py <image_path_or_url> <lat> <lon> <YYYY-MM-DD>",
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
    )

    print(f"Submitting {claim.claim_id} (requesting ${claim.estimated_loss_usd:.2f})...")
    record = insurer.submit(claim)
    print(json.dumps(record, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
