"""Multimodal crop damage assessor — Qwen-VL based."""

from __future__ import annotations

import json
from pathlib import Path

from app.clients.qwen import encode_image, vision_chat
from app.models.damage import DamageAssessment

SYSTEM_PROMPT = """\
You are a crop insurance damage assessor working for smallholder farmer claims.

You will be shown ONE photo of a farm field. Your job is to identify:
- the crop in the photo
- whether visible damage is present
- the primary cause of that damage (flood, drought, hail, wind, fire, frost, pest, disease, other)
- a severity score (0 = healthy, 100 = total loss)
- the percentage of the visible area that is affected
- your confidence in the verdict

Be conservative. If you cannot tell, say so via low confidence and damage_cause="unknown".
Never invent symptoms that are not visible in the photo.
Return STRICT JSON only.
"""

USER_PROMPT = """\
Assess this farm photo and return a JSON object with EXACTLY these fields:

{
  "crop_type": "string (best-guess crop, e.g. 'rice', 'wheat', 'maize', 'cotton', 'unknown')",
  "damage_cause": "one of: flood, drought, hail, wind, fire, frost, pest, disease, other, unknown",
  "severity": 0-100 integer,
  "affected_area_pct": 0-100 integer,
  "confidence": 0.0-1.0 float,
  "visible_indicators": ["short phrase", "short phrase"],
  "notes": "one-line plain English summary"
}

Return ONLY the JSON object. No prose, no markdown fences.
"""


def assess_damage(image_path_or_url: str) -> DamageAssessment:
    """Run Qwen-VL on a photo and return a structured damage assessment.

    `image_path_or_url` may be a local file path or a public https URL.
    """
    if image_path_or_url.startswith(("http://", "https://", "data:")):
        image = image_path_or_url
    else:
        if not Path(image_path_or_url).exists():
            raise FileNotFoundError(image_path_or_url)
        image = encode_image(image_path_or_url)

    raw = vision_chat(system=SYSTEM_PROMPT, user_text=USER_PROMPT, image=image, json_mode=True)
    data = json.loads(raw)
    return DamageAssessment(**data)
