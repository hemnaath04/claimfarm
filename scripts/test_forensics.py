"""Smoke-test the photo forensics pipeline on a local image.

Usage:
    uv run python scripts/test_forensics.py path/to/photo.jpg
"""

from __future__ import annotations

import base64
import sys

from dotenv import load_dotenv

load_dotenv()

from app.agents import photo_forensics


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: test_forensics.py <image_path>", file=sys.stderr)
        return 2
    path = sys.argv[1]
    with open(path, "rb") as fh:
        photo_bytes = fh.read()
    suffix = path.rsplit(".", 1)[-1].lower()
    if suffix == "jpg":
        suffix = "jpeg"
    image_data_url = (
        f"data:image/{suffix};base64," + base64.b64encode(photo_bytes).decode("ascii")
    )
    result = photo_forensics.analyze(photo_bytes, image_data_url)
    print(result.model_dump_json(indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
