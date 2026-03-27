from fastapi import APIRouter

from app.services.system_monitor import get_system_stats
from app.services.weather import fetch_weather
from app.services.github import fetch_github_events
from app.services.cricket import fetch_cricket_scores
from app.services.news import fetch_news
from app.services.trending import fetch_github_trending
from app.services.lofi import get_lofi_scene
from app.scheduler import get_all_cached
from app.config import get_settings

settings = get_settings()

router = APIRouter(prefix="/api")


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/widgets")
async def widgets_snapshot():
    """Return the latest cached data for all widgets."""
    return get_all_cached()


@router.get("/system")
async def system():
    import asyncio

    return await asyncio.to_thread(get_system_stats)


@router.get("/weather")
async def weather(city: str = "Hyderabad,IN"):
    return await fetch_weather(city)


@router.get("/github")
async def github(username: str = settings.github_username):
    return await fetch_github_events(username)


@router.get("/cricket")
async def cricket():
    return await fetch_cricket_scores()


@router.get("/news")
async def news(category: str = "technology"):
    return await fetch_news(category)


@router.get("/trending")
async def trending(language: str = "", since: str = "daily"):
    return await fetch_github_trending(language, since)


@router.get("/lofi")
async def lofi():
    return get_lofi_scene()
