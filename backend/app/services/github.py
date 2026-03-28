import httpx
import logging
import re
from datetime import date, datetime, timedelta

from app.config import get_settings

logger = logging.getLogger("glanceos.github")
CONTRIBUTION_WEEKS = 10


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
    contributions_ok = False
    source = "unavailable"

    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        try:
            events = await _fetch_events(client, username, headers)
        except Exception as exc:
            logger.warning("GitHub events fetch failed for %s: %s", username, exc)

        try:
            contributions = await _fetch_contributions(client, username, headers)
            contributions_ok = True
        except Exception as exc:
            logger.warning("GitHub contributions fetch failed for %s: %s", username, exc)

    if events or contributions_ok:
        source = "live"

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
    window_start = today - timedelta(days=(7 * CONTRIBUTION_WEEKS) - 1)
    url = f"https://github.com/users/{username}/contributions"

    contribution_headers = {
        "User-Agent": headers.get("User-Agent", "GlanceOS/0.1"),
        "Accept": "image/svg+xml,text/html;q=0.9,*/*;q=0.8",
    }

    resp = await client.get(
        url,
        params={"from": window_start.isoformat(), "to": today.isoformat()},
        headers=contribution_headers,
    )
    resp.raise_for_status()

    svg = resp.text
    day_tag_pattern = re.compile(
        r"<[^>]*\bdata-date=[\"']([0-9]{4}-[0-9]{2}-[0-9]{2})[\"'][^>]*>",
        flags=re.IGNORECASE,
    )
    level_pattern = re.compile(r"data-level=[\"']([0-9]+)[\"']")
    count_pattern = re.compile(r"data-count=[\"']([0-9]+)[\"']")

    cells: list[tuple[str, int]] = []
    for day_tag_match in day_tag_pattern.finditer(svg):
        day_tag = day_tag_match.group(0)
        day_date = day_tag_match.group(1)

        level_match = level_pattern.search(day_tag)
        if level_match:
            level = int(level_match.group(1))
        else:
            count_match = count_pattern.search(day_tag)
            count = int(count_match.group(1)) if count_match else 0
            if count <= 0:
                level = 0
            elif count < 3:
                level = 1
            elif count < 6:
                level = 2
            elif count < 10:
                level = 3
            else:
                level = 4

        cells.append((day_date, max(0, min(level, 4))))

    if not cells:
        return _empty_contributions(today)

    day_levels: dict[date, int] = {}
    for date_str, level in cells:
        try:
            day = date.fromisoformat(date_str)
            day_levels[day] = level
        except ValueError:
            continue

    if not day_levels:
        return _empty_contributions(today)

    levels: list[int] = []
    cursor = window_start
    while cursor <= today:
        levels.append(day_levels.get(cursor, 0))
        cursor += timedelta(days=1)

    weeks: list[list[int]] = []
    for idx in range(0, len(levels), 7):
        weeks.append(levels[idx : idx + 7])

    if len(weeks) < CONTRIBUTION_WEEKS:
        padding = [[0, 0, 0, 0, 0, 0, 0] for _ in range(CONTRIBUTION_WEEKS - len(weeks))]
        weeks = padding + weeks
    else:
        weeks = weeks[-CONTRIBUTION_WEEKS:]

    return {
        "weeks": weeks,
        "max_level": 4,
        "from": window_start.isoformat(),
        "to": today.isoformat(),
    }


def _empty_contributions(today: date | None = None) -> dict:
    today = today or date.today()
    window_start = today - timedelta(days=(7 * CONTRIBUTION_WEEKS) - 1)

    return {
        "weeks": [[0, 0, 0, 0, 0, 0, 0] for _ in range(CONTRIBUTION_WEEKS)],
        "max_level": 4,
        "from": window_start.isoformat(),
        "to": today.isoformat(),
    }
