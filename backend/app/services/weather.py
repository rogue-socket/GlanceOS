import httpx
import logging
from app.config import get_settings

logger = logging.getLogger("glanceos.weather")


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
                "description": raw["weather"][0]["description"],
                "icon": raw["weather"][0]["icon"],
                "source": "live",
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
        "description": reason,
        "icon": "01d",
        "source": "offline",
    }
