"""Quick CLI for the damage assessor.

Usage:
    uv run python scripts/test_damage.py path/to/photo.jpg
    uv run python scripts/test_damage.py https://example.com/photo.jpg
"""

from __future__ import annotations

import sys

from dotenv import load_dotenv

load_dotenv()

from app.agents.damage_assessor import assess_damage


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: test_damage.py <image_path_or_url>", file=sys.stderr)
        return 2
    result = assess_damage(sys.argv[1])
    print(result.model_dump_json(indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
