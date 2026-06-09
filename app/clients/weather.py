"""Open-Meteo historical weather client + aggregation."""

from __future__ import annotations

from datetime import date, timedelta

import httpx

from app.config import get_settings
from app.models.weather import WeatherSummary


def _fetch_daily(lat: float, lon: float, start: date, end: date) -> dict:
    s = get_settings()
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "daily": ",".join(
            [
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_sum",
                "wind_speed_10m_max",
            ]
        ),
        "timezone": "auto",
    }
    r = httpx.get(s.open_meteo_base, params=params, timeout=20.0)
    r.raise_for_status()
    return r.json()


def _max_run(values: list[float], predicate) -> int:
    best = run = 0
    for v in values:
        if predicate(v):
            run += 1
            best = max(best, run)
        else:
            run = 0
    return best


def summarize_window(
    lat: float, lon: float, end: date, lookback_days: int = 30
) -> WeatherSummary:
    """Pull `lookback_days` of daily weather ending on `end` and aggregate."""
    start = end - timedelta(days=lookback_days - 1)
    data = _fetch_daily(lat, lon, start, end)
    daily = data.get("daily", {})

    tmax = [x for x in daily.get("temperature_2m_max") or [] if x is not None]
    tmin = [x for x in daily.get("temperature_2m_min") or [] if x is not None]
    precip = [x for x in daily.get("precipitation_sum") or [] if x is not None]
    wind = [x for x in daily.get("wind_speed_10m_max") or [] if x is not None]

    return WeatherSummary(
        latitude=lat,
        longitude=lon,
        start_date=start,
        end_date=end,
        total_precip_mm=round(sum(precip), 1),
        max_temp_c=round(max(tmax) if tmax else 0.0, 1),
        min_temp_c=round(min(tmin) if tmin else 0.0, 1),
        max_wind_kmh=round(max(wind) if wind else 0.0, 1),
        days_above_35c=sum(1 for t in tmax if t > 35.0),
        days_with_heavy_rain=sum(1 for p in precip if p > 30.0),
        days_with_frost=sum(1 for t in tmin if t < 0.0),
        consecutive_dry_days=_max_run(precip, lambda p: p < 1.0),
    )
