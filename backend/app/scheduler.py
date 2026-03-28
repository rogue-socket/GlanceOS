from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from collections import defaultdict

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.services.system_monitor import get_system_stats
from app.services.weather import fetch_weather
from app.services.github import fetch_github_events
from app.services.cricket import fetch_cricket_scores
from app.services.news import fetch_news
from app.services.trending import fetch_github_trending
from app.services.f1 import fetch_f1_data
from app.services.lofi import get_lofi_scene
from app.services.calendar import fetch_calendar_events
from app.services.todoist import fetch_todoist_tasks
from app.config import get_settings
from app.ws_manager import manager

logger = logging.getLogger("glanceos.scheduler")
settings = get_settings()

scheduler = AsyncIOScheduler()

# In-memory cache of latest data for each widget type
_cache: dict[str, dict] = {}
_api_call_counts: dict[str, int] = defaultdict(int)

API_JOB_INTERVAL_SECONDS = {
    "weather": 300,
    "github": 300,
    "cricket": 120,
    "news": 900,
    "trending": 1800,
    "f1": 300,
    "calendar": 300,
    "todo": 120,
}

ANSI_RESET = "\033[0m"


def _format_interval(seconds: int) -> str:
    if seconds % 3600 == 0:
        return f"{seconds // 3600}h"
    if seconds % 60 == 0:
        return f"{seconds // 60}m"
    return f"{seconds}s"


def _cadence_style(seconds: int) -> tuple[str, str]:
    if seconds <= 120:
        return "\033[38;5;208m", "high"
    if seconds <= 600:
        return "\033[93m", "medium"
    return "\033[92m", "low"


def _log_api_tick(widget: str) -> None:
    interval = API_JOB_INTERVAL_SECONDS.get(widget)
    if not interval:
        return

    _api_call_counts[widget] += 1
    color, band = _cadence_style(interval)
    print(
        f"{color}[api:{widget}] {band} q{_format_interval(interval)} #{_api_call_counts[widget]}{ANSI_RESET}"
    )


def _log_api_cadence_legend() -> None:
    print("\033[38;5;208m[api] high<=2m\033[0m \033[93mmedium<=10m\033[0m \033[92mlow>10m\033[0m")


def get_cached(widget_type: str) -> dict | None:
    return _cache.get(widget_type)


def get_all_cached() -> dict:
    return dict(_cache)


# ── Jobs ──────────────────────────────────────────────


async def _push_system_stats() -> None:
    try:
        data = await asyncio.to_thread(get_system_stats)
        _cache["system"] = data
        await manager.broadcast(data)
    except Exception:
        logger.debug("Failed to push system stats")


async def _push_weather() -> None:
    try:
        _log_api_tick("weather")
        data = await fetch_weather(settings.weather_city)
        _cache["weather"] = data
        await manager.broadcast(data)
    except Exception:
        logger.debug("Failed to push weather")


async def _push_github() -> None:
    try:
        _log_api_tick("github")
        data = await fetch_github_events(settings.github_username)
        _cache["github"] = data
        await manager.broadcast(data)
    except Exception:
        logger.debug("Failed to push GitHub events")


async def _push_clock() -> None:
    data = {"type": "clock", "data": {"iso": datetime.utcnow().isoformat()}}
    _cache["clock"] = data
    await manager.broadcast(data)


async def _push_cricket() -> None:
    try:
        _log_api_tick("cricket")
        data = await fetch_cricket_scores(settings.cricket_api_key)
        _cache["cricket"] = data
        await manager.broadcast(data)
    except Exception:
        logger.debug("Failed to push cricket scores")


async def _push_news() -> None:
    try:
        _log_api_tick("news")
        data = await fetch_news()
        _cache["news"] = data
        await manager.broadcast(data)
    except Exception:
        logger.debug("Failed to push news")


async def _push_trending() -> None:
    try:
        _log_api_tick("trending")
        data = await fetch_github_trending()
        _cache["trending"] = data
        await manager.broadcast(data)
    except Exception:
        logger.debug("Failed to push trending")


async def _push_f1() -> None:
    try:
        _log_api_tick("f1")
        data = await fetch_f1_data()
        _cache["f1"] = data
        await manager.broadcast(data)
    except Exception:
        logger.debug("Failed to push f1")


async def _push_lofi() -> None:
    try:
        data = await asyncio.to_thread(get_lofi_scene)
        _cache["lofi"] = data
        await manager.broadcast(data)
    except Exception:
        logger.debug("Failed to push lofi scene")


async def _push_calendar() -> None:
    try:
        _log_api_tick("calendar")
        data = await fetch_calendar_events()
        _cache["calendar"] = data
        await manager.broadcast(data)
    except Exception:
        logger.debug("Failed to push calendar events")


async def _push_todo() -> None:
    try:
        _log_api_tick("todo")
        data = await fetch_todoist_tasks()
        _cache["todo"] = data
        await manager.broadcast(data)
    except Exception:
        logger.debug("Failed to push todo tasks")


# ── Lifecycle ─────────────────────────────────────────


def start_scheduler() -> None:
    now = datetime.utcnow()
    _log_api_cadence_legend()

    scheduler.add_job(_push_clock, "interval", seconds=1, id="clock")
    scheduler.add_job(_push_system_stats, "interval", seconds=3, id="system")
    scheduler.add_job(_push_weather, "interval", minutes=5, id="weather", next_run_time=now)
    scheduler.add_job(_push_github, "interval", minutes=5, id="github", next_run_time=now)
    scheduler.add_job(_push_cricket, "interval", minutes=2, id="cricket", next_run_time=now)
    scheduler.add_job(_push_news, "interval", minutes=15, id="news", next_run_time=now)
    scheduler.add_job(_push_trending, "interval", minutes=30, id="trending", next_run_time=now)
    scheduler.add_job(_push_f1, "interval", minutes=5, id="f1", next_run_time=now)
    scheduler.add_job(_push_lofi, "interval", seconds=30, id="lofi", next_run_time=now)
    scheduler.add_job(_push_calendar, "interval", minutes=5, id="calendar", next_run_time=now)
    scheduler.add_job(_push_todo, "interval", minutes=2, id="todo", next_run_time=now)
    scheduler.start()
    logger.info("Scheduler started")


def stop_scheduler() -> None:
    scheduler.shutdown(wait=False)
    logger.info("Scheduler stopped")
