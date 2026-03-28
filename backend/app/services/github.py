import httpx
import logging
import re
from datetime import date, datetime, timedelta

from app.config import get_settings

logger = logging.getLogger("glanceos.github")


async def fetch_github_events(username: str = "octocat") -> dict:
    """Fetch GitHub profile activity and contribution graph."""
    settings = get_settings()
    username = (username or "octocat").strip() or "octocat"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "GlanceOS/0.1",
    }
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"

    events: list[dict] = []
    contributions = _empty_contributions()
    source = "unavailable"

    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            events = await _fetch_events(client, username, headers)
            contributions = await _fetch_contributions(client, username, headers)
        if events or contributions["weeks"]:
            source = "live"
    except Exception as exc:
        logger.warning("GitHub fetch failed for %s: %s", username, exc)

    return {
        "type": "github",
        "data": {
            "username": username,
            "events": events,
            "contributions": contributions,
            "source": source,
        },
    }


async def _fetch_events(client: httpx.AsyncClient, username: str, headers: dict[str, str]) -> list[dict]:
    url = f"https://api.github.com/users/{username}/events"
    resp = await client.get(url, headers=headers, params={"per_page": 10})
    resp.raise_for_status()
    events = resp.json()

    parsed_events = [
        {
            "id": e.get("id", f"evt-{idx}"),
            "type": e.get("type", "Event"),
            "repo": e.get("repo", {}).get("name", "unknown/repo"),
            "created_at": e.get("created_at"),
        }
        for idx, e in enumerate(events[:10])
    ]

    return parsed_events


async def _fetch_contributions(
    client: httpx.AsyncClient, username: str, headers: dict[str, str]
) -> dict:
    today = date.today()
    start = today - timedelta(days=7 * 20)
    url = f"https://github.com/users/{username}/contributions"

    resp = await client.get(
        url,
        params={"from": start.isoformat(), "to": today.isoformat()},
        headers=headers,
    )
    resp.raise_for_status()

    svg = resp.text
    pattern = re.compile(
        r"data-date=[\"']([0-9]{4}-[0-9]{2}-[0-9]{2})[\"'][^>]*data-level=[\"']([0-4])[\"']"
    )
    matches = pattern.findall(svg)
    if not matches:
        return _empty_contributions()

    day_levels: dict[date, int] = {}
    for date_str, level_str in matches:
        try:
            day = date.fromisoformat(date_str)
            day_levels[day] = int(level_str)
        except ValueError:
            continue

    if not day_levels:
        return _empty_contributions()

    first_day = min(day_levels.keys())
    last_day = max(day_levels.keys())

    # GitHub contribution weeks are Sunday-aligned columns.
    start_offset = (first_day.weekday() + 1) % 7
    start_aligned = first_day - timedelta(days=start_offset)

    end_offset = (6 - ((last_day.weekday() + 1) % 7)) % 7
    end_aligned = last_day + timedelta(days=end_offset)

    levels: list[int] = []
    cursor = start_aligned
    while cursor <= end_aligned:
        levels.append(day_levels.get(cursor, 0))
        cursor += timedelta(days=1)

    weeks: list[list[int]] = []
    for idx in range(0, len(levels), 7):
        weeks.append(levels[idx : idx + 7])

    return {
        "weeks": weeks[-20:],
        "max_level": 4,
        "from": start.isoformat(),
        "to": today.isoformat(),
    }


def _empty_contributions() -> dict:
    return {
        "weeks": [],
        "max_level": 4,
        "from": None,
        "to": None,
    }
