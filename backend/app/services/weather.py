import httpx
import logging
from datetime import datetime, timezone
from app.config import get_settings

logger = logging.getLogger("glanceos.weather")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _to_kph(speed_mps: float | int | None) -> float | None:
    if speed_mps is None:
        return None
    try:
        return round(float(speed_mps) * 3.6, 1)
    except (TypeError, ValueError):
        return None


async def fetch_weather(city: str = "Hyderabad,IN") -> dict:
    """Fetch weather from OpenWeatherMap. Falls back to offline placeholder."""
    settings = get_settings()
    api_key = settings.weather_api_key
    if not api_key:
        return {
            "type": "weather",
            "data": _get_offline_weather(city, reason="No API key configured"),
        }

    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {"q": city, "appid": api_key, "units": "metric"}

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            raw = resp.json()

        return {
            "type": "weather",
            "data": {
                "city": raw.get("name", city),
                "temp": raw["main"]["temp"],
                "feels_like": raw["main"]["feels_like"],
                "humidity": raw["main"]["humidity"],
                "pressure_hpa": raw["main"].get("pressure"),
                "description": raw["weather"][0]["description"],
                "icon": raw["weather"][0]["icon"],
                "wind_kph": _to_kph(raw.get("wind", {}).get("speed")),
                "wind_deg": raw.get("wind", {}).get("deg"),
                "visibility_km": round(raw.get("visibility", 0) / 1000, 1) if raw.get("visibility") is not None else None,
                "source": "live",
                "fetched_at": _utc_now_iso(),
            },
        }
    except Exception:
        logger.debug("Weather API failed, using offline data")

    return {
        "type": "weather",
        "data": _get_offline_weather(city, reason="API unavailable"),
    }


def _get_offline_weather(city: str, reason: str) -> dict:
    return {
        "city": city,
        "temp": "--",
        "feels_like": "--",
        "humidity": "--",
        "pressure_hpa": None,
        "description": reason,
        "icon": "01d",
        "wind_kph": None,
        "wind_deg": None,
        "visibility_km": None,
        "source": "offline",
        "fetched_at": _utc_now_iso(),
        "reason": reason,
    }
