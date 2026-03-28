from fastapi import APIRouter

from app.services.system_monitor import get_system_stats
from app.services.weather import fetch_weather
from app.services.github import fetch_github_events
from app.services.news import fetch_news
from app.services.trending import fetch_github_trending
from app.services.f1 import fetch_f1_data
from app.services.lofi import get_lofi_scene
from app.services.calendar import fetch_calendar_events
from app.services.todoist import fetch_todoist_tasks
from app.scheduler import cricket_schedule_meta, get_all_cached, get_cached, refresh_cricket_now
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
    cached = get_cached("cricket")
    if cached:
        if isinstance(cached, dict) and isinstance(cached.get("data"), dict):
            cached["data"].setdefault("schedule", cricket_schedule_meta())
        return cached

    return {
        "type": "cricket",
        "data": {
            "matches": [],
            "source": "cache",
            "status": "empty",
            "message": "No cached cricket data yet",
            "schedule": cricket_schedule_meta(),
        },
    }


@router.post("/cricket/refresh")
async def cricket_refresh():
    return await refresh_cricket_now()


@router.get("/news")
async def news(category: str = "technology"):
    return await fetch_news(category)


@router.get("/trending")
async def trending(language: str = "", since: str = "daily"):
    return await fetch_github_trending(language, since)


@router.get("/f1")
async def f1():
    return await fetch_f1_data()


@router.get("/lofi")
async def lofi():
    return get_lofi_scene()


@router.get("/calendar")
async def calendar():
    return await fetch_calendar_events()


@router.get("/todo")
async def todo():
    return await fetch_todoist_tasks()
