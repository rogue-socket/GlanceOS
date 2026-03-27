import httpx
from app.config import get_settings


async def fetch_weather(city: str = "London") -> dict:
    settings = get_settings()
    api_key = settings.weather_api_key
    if not api_key:
        return {
            "type": "weather",
            "data": {"error": "No API key configured", "city": city},
        }

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
        },
    }
