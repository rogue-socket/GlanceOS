from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.services.system_monitor import get_system_stats
from app.services.weather import fetch_weather
from app.services.github import fetch_github_events
from app.services.cricket import fetch_cricket_scores
from app.services.news import fetch_news
from app.services.trending import fetch_github_trending
from app.services.lofi import get_lofi_scene
from app.ws_manager import manager

logger = logging.getLogger("glanceos.scheduler")

scheduler = AsyncIOScheduler()

# In-memory cache of latest data for each widget type
_cache: dict[str, dict] = {}


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
        logger.exception("Failed to push system stats")


async def _push_weather() -> None:
    try:
        data = await fetch_weather()
        _cache["weather"] = data
        await manager.broadcast(data)
    except Exception:
        logger.exception("Failed to push weather")


async def _push_github() -> None:
    try:
        data = await fetch_github_events()
        _cache["github"] = data
        await manager.broadcast(data)
    except Exception:
        logger.exception("Failed to push GitHub events")


async def _push_clock() -> None:
    data = {"type": "clock", "data": {"iso": datetime.utcnow().isoformat()}}
    _cache["clock"] = data
    await manager.broadcast(data)


async def _push_cricket() -> None:
    try:
        data = await fetch_cricket_scores()
        _cache["cricket"] = data
        await manager.broadcast(data)
    except Exception:
        logger.exception("Failed to push cricket scores")


async def _push_news() -> None:
    try:
        data = await fetch_news()
        _cache["news"] = data
        await manager.broadcast(data)
    except Exception:
        logger.exception("Failed to push news")


async def _push_trending() -> None:
    try:
        data = await fetch_github_trending()
        _cache["trending"] = data
        await manager.broadcast(data)
    except Exception:
        logger.exception("Failed to push trending")


async def _push_lofi() -> None:
    try:
        data = await asyncio.to_thread(get_lofi_scene)
        _cache["lofi"] = data
        await manager.broadcast(data)
    except Exception:
        logger.exception("Failed to push lofi scene")


# ── Lifecycle ─────────────────────────────────────────


def start_scheduler() -> None:
    scheduler.add_job(_push_clock, "interval", seconds=1, id="clock")
    scheduler.add_job(_push_system_stats, "interval", seconds=3, id="system")
    scheduler.add_job(_push_weather, "interval", minutes=10, id="weather")
    scheduler.add_job(_push_github, "interval", minutes=5, id="github")
    scheduler.add_job(_push_cricket, "interval", minutes=2, id="cricket")
    scheduler.add_job(_push_news, "interval", minutes=15, id="news")
    scheduler.add_job(_push_trending, "interval", minutes=30, id="trending")
    scheduler.add_job(_push_lofi, "interval", seconds=30, id="lofi")
    scheduler.start()
    logger.info("Scheduler started")


def stop_scheduler() -> None:
    scheduler.shutdown(wait=False)
    logger.info("Scheduler stopped")
