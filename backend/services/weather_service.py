"""Weather service using OpenWeatherMap forecast API."""
from __future__ import annotations
import logging
from datetime import date
from typing import Optional

import httpx

from backend.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


async def get_weather_forecast(city: str, trip_start: date, trip_end: date) -> dict:
    """Return a simplified weather summary for the trip period."""
    if not settings.openweather_api_key:
        return {"summary": "Weather data unavailable (no API key configured).", "days": []}

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{settings.openweather_base_url}/forecast",
                params={
                    "q": city,
                    "appid": settings.openweather_api_key,
                    "units": "metric",
                    "cnt": 40,
                },
            )
            resp.raise_for_status()
            data = resp.json()

        days: dict[str, list] = {}
        for item in data.get("list", []):
            dt_txt: str = item["dt_txt"][:10]  # YYYY-MM-DD
            d = date.fromisoformat(dt_txt)
            if trip_start <= d <= trip_end:
                days.setdefault(dt_txt, []).append(item)

        summaries = []
        for day_str, readings in sorted(days.items()):
            descriptions = [r["weather"][0]["description"] for r in readings]
            temps = [r["main"]["temp"] for r in readings]
            rain = any("rain" in d or "storm" in d for d in descriptions)
            summaries.append({
                "date": day_str,
                "avg_temp_c": round(sum(temps) / len(temps), 1),
                "conditions": descriptions,
                "rain_likely": rain,
            })

        overall = "generally pleasant"
        rainy_days = sum(1 for s in summaries if s["rain_likely"])
        if rainy_days > len(summaries) / 2:
            overall = "expect significant rain – pack accordingly"
        elif rainy_days > 0:
            overall = f"mixed weather with rain on ~{rainy_days} day(s)"

        return {
            "summary": f"Weather forecast for {city}: {overall}.",
            "days": summaries,
        }

    except Exception as exc:
        logger.warning("Weather fetch failed for %s: %s", city, exc)
        return {"summary": "Weather forecast temporarily unavailable.", "days": []}
