"""Cross-reference damage against historical weather.

Usage:
    uv run python scripts/test_weather.py <image_path_or_url> <lat> <lon> <YYYY-MM-DD>
"""

from __future__ import annotations

import sys
from datetime import date

from dotenv import load_dotenv

load_dotenv()

from app.agents.damage_assessor import assess_damage
from app.agents.weather_corroborator import corroborate


def main() -> int:
    if len(sys.argv) < 5:
        print(
            "usage: test_weather.py <image_path_or_url> <lat> <lon> <YYYY-MM-DD>",
            file=sys.stderr,
        )
        return 2
    image, lat_s, lon_s, date_s = sys.argv[1:5]
    lat = float(lat_s)
    lon = float(lon_s)
    claim_date = date.fromisoformat(date_s)

    damage = assess_damage(image)
    print("=== Damage assessment ===")
    print(damage.model_dump_json(indent=2))

    weather, corr = corroborate(damage, latitude=lat, longitude=lon, claim_date=claim_date)
    print("\n=== Weather summary ===")
    print(weather.model_dump_json(indent=2))
    print("\n=== Corroboration ===")
    print(corr.model_dump_json(indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
