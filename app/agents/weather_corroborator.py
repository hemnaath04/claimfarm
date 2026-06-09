"""Cross-references a damage assessment against recent weather data."""

from __future__ import annotations

import json
from datetime import date

from app.clients.qwen import text_chat
from app.clients.weather import summarize_window
from app.models.damage import DamageAssessment
from app.models.weather import CorroborationResult, WeatherSummary

SYSTEM_PROMPT = """\
You are an agricultural insurance adjuster's research assistant.

You will be given (1) a visual damage assessment of a farm field, and
(2) a 30-day weather summary for that field's location ending on the claim date.

Decide whether the weather data plausibly supports the proposed damage cause.
Be specific. If the cause is "drought" you should see low precip and/or hot days.
If it's "flood" you should see heavy rain. If it's "frost" you should see sub-zero
temps. If the weather contradicts the visual verdict, flag it.

Return STRICT JSON only.
"""


def _build_user_prompt(damage: DamageAssessment, weather: WeatherSummary) -> str:
    return f"""\
Damage assessment:
{damage.model_dump_json(indent=2)}

Weather summary (30 days ending {weather.end_date.isoformat()}):
{weather.model_dump_json(indent=2)}

Return JSON with EXACTLY these fields:
{{
  "corroborated": true | false,
  "strength": 0.0-1.0,
  "evidence": "one-line summary linking weather to damage",
  "flags": ["short phrase per inconsistency (empty list if none)"]
}}

Return ONLY the JSON object.
"""


def corroborate(
    damage: DamageAssessment,
    *,
    latitude: float,
    longitude: float,
    claim_date: date,
    lookback_days: int = 30,
) -> tuple[WeatherSummary, CorroborationResult]:
    weather = summarize_window(latitude, longitude, claim_date, lookback_days)
    raw = text_chat(
        system=SYSTEM_PROMPT,
        user_text=_build_user_prompt(damage, weather),
        json_mode=True,
        temperature=0.1,
    )
    result = CorroborationResult(**json.loads(raw))
    return weather, result
