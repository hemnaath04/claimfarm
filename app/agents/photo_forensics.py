"""Photo forensics: EXIF metadata + Qwen-VL authenticity check.

Surfaces signal that an adjuster can use to decide how much to trust a
submitted photo before approving the claim. Two passes:

1. Cheap, local: parse EXIF (capture time, GPS, camera make/model, edit
   software, image dimensions).
2. LLM call: ask Qwen-VL whether the image looks like a real phone photo
   of a real field, or whether it looks like a screenshot / render / AI
   generation. Returns a confidence score + reasoning.

The combined result feeds a list of `flags` like 'exif_stripped',
'edit_software_detected', 'authenticity_low', which appear in the
adjuster dashboard alongside fraud_check results.
"""

from __future__ import annotations

import io
import json
import logging
from datetime import datetime
from fractions import Fraction
from typing import Any

from PIL import ExifTags, Image

from app.clients.qwen import vision_chat
from app.models.forensics import PhotoForensics

logger = logging.getLogger(__name__)

# -------- EXIF helpers ----------------------------------------------------


def _rational_to_float(value: Any) -> float | None:
    """Convert an EXIF rational/tuple to a float."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, Fraction):
        return float(value)
    if isinstance(value, tuple) and len(value) == 2:
        try:
            num, den = value
            return float(num) / float(den) if den else None
        except Exception:
            return None
    try:
        return float(value)
    except Exception:
        return None


def _dms_to_deg(dms: Any, ref: str | None) -> float | None:
    """Convert EXIF (deg, min, sec) tuples + N/S/E/W reference to signed decimal."""
    if not isinstance(dms, (list, tuple)) or len(dms) < 3:
        return None
    parts = [_rational_to_float(x) for x in dms]
    if any(p is None for p in parts):
        return None
    d, m, s = parts
    val = d + m / 60.0 + s / 3600.0
    if isinstance(ref, str) and ref.upper() in ("S", "W"):
        val = -val
    return round(val, 6)


def _parse_exif_datetime(s: str | None) -> datetime | None:
    if not s:
        return None
    for fmt in ("%Y:%m:%d %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y:%m:%dT%H:%M:%S"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def extract_exif(image_bytes: bytes) -> dict:
    """Return a flat dict of the EXIF fields we care about. Empty dict if no EXIF."""
    out: dict[str, Any] = {}
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            out["width"], out["height"] = img.size
            raw = img.getexif() if hasattr(img, "getexif") else None
            if not raw:
                return out

            tag_map = {ExifTags.TAGS.get(tid, tid): v for tid, v in raw.items()}
            out["camera_make"] = tag_map.get("Make")
            out["camera_model"] = tag_map.get("Model")
            out["software"] = tag_map.get("Software")
            out["capture_time"] = _parse_exif_datetime(
                tag_map.get("DateTimeOriginal") or tag_map.get("DateTime")
            )

            gps_info_id = next(
                (tid for tid, name in ExifTags.TAGS.items() if name == "GPSInfo"), None
            )
            gps_block = raw.get_ifd(gps_info_id) if gps_info_id is not None else None
            if gps_block:
                gps_tags = {
                    ExifTags.GPSTAGS.get(tid, tid): v for tid, v in gps_block.items()
                }
                out["gps_lat"] = _dms_to_deg(
                    gps_tags.get("GPSLatitude"), gps_tags.get("GPSLatitudeRef")
                )
                out["gps_lon"] = _dms_to_deg(
                    gps_tags.get("GPSLongitude"), gps_tags.get("GPSLongitudeRef")
                )
    except Exception:
        logger.exception("EXIF parse failed; returning what we have")
    return out


# -------- Qwen-VL authenticity check --------------------------------------

_AUTH_SYSTEM = """\
You are an image forensics assistant. You judge whether an image looks like
a real phone-camera photo of a real outdoor scene, or whether it looks like
a screenshot, web download, AI generation, render, or composite.

Be conservative. If you cannot tell, default to appears_real_phone_photo=true
with a moderate score (around 0.6) and note the uncertainty.
Return STRICT JSON.
"""

_AUTH_USER = """\
Look at the image carefully. Specifically check for:

1. Watermarks or text overlays: any "alamy", "shutterstock", "getty", "dreamstime",
   "istock", "depositphotos", website URLs, image IDs printed on the image,
   logos overlaid on the photo. ANY of these strongly indicates a stock /
   licensed image, not a farmer's phone photo. Score must be ≤ 0.3.
2. Screenshot UI: notification bars, status bars, app chrome at top/bottom.
3. AI generation tells: unnatural smoothness, six-fingered hands, repeating
   patterns, hyper-saturated colors.
4. Composite/rendered look: inconsistent lighting between subjects.

If the image looks like an organic, low-friction smartphone capture of a real
outdoor scene, score ≥ 0.7.

Return JSON with EXACTLY these fields:
{
  "appears_real_phone_photo": true | false,
  "score": 0.0-1.0,
  "reasoning": "one short sentence — name any watermark text you see verbatim"
}

Return ONLY the JSON object.
"""


def _qwen_authenticity(image_data_url: str) -> tuple[bool, float, str]:
    try:
        raw = vision_chat(
            system=_AUTH_SYSTEM,
            user_text=_AUTH_USER,
            image=image_data_url,
            json_mode=True,
            max_tokens=200,
            temperature=0.0,
        )
        data = json.loads(raw)
        return (
            bool(data.get("appears_real_phone_photo", True)),
            float(data.get("score", 0.5)),
            str(data.get("reasoning", "")),
        )
    except Exception:
        logger.exception("authenticity check failed; treating as 'unknown'")
        return True, 0.5, "authenticity check failed"


# -------- Combined entry point --------------------------------------------


def analyze(image_bytes: bytes, image_data_url: str) -> PhotoForensics:
    """EXIF + Qwen-VL authenticity, packed into one PhotoForensics record."""
    exif = extract_exif(image_bytes)
    appears_real, score, reasoning = _qwen_authenticity(image_data_url)

    flags: list[str] = []
    if not exif.get("camera_make") and not exif.get("capture_time"):
        flags.append("exif_stripped")
    sw = (exif.get("software") or "").lower()
    if any(k in sw for k in ("photoshop", "snapseed", "lightroom", "gimp", "ai")):
        flags.append(f"edit_software:{exif.get('software')}")
    if not appears_real or score < 0.45:
        flags.append("authenticity_low")
    if exif.get("gps_lat") is None:
        flags.append("no_gps_in_exif")

    return PhotoForensics(
        has_exif=bool(exif.get("camera_make") or exif.get("capture_time")),
        capture_time=exif.get("capture_time"),
        gps_lat=exif.get("gps_lat"),
        gps_lon=exif.get("gps_lon"),
        camera_make=exif.get("camera_make"),
        camera_model=exif.get("camera_model"),
        software=exif.get("software"),
        width=exif.get("width"),
        height=exif.get("height"),
        file_size_bytes=len(image_bytes),
        appears_real_phone_photo=appears_real,
        authenticity_score=score,
        authenticity_reasoning=reasoning,
        flags=flags,
    )
