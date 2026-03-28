import httpx
import logging
from datetime import datetime, timedelta, timezone

from app.config import get_settings

logger = logging.getLogger("glanceos.trending")


async def fetch_github_trending(language: str = "", since: str = "daily") -> dict:
    """Fetch trending repositories using live GitHub-backed sources only."""

    settings = get_settings()
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "GlanceOS/0.1",
    }
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"

    try:
        return await _fetch_from_github_search(language, since, headers)
    except Exception as exc:
        logger.warning("Trending fetch failed: %s", exc)

    try:
        return await _fetch_trending_api(language, since)
    except Exception as exc:
        logger.warning("Fallback trending fetch failed: %s", exc)

    return {
        "type": "trending",
        "data": {
            "repos": [],
            "language": language or "all",
            "since": since,
            "source": "unavailable",
            "error": "Live trending sources unavailable",
        },
    }


def _since_days(since: str) -> int:
    normalized = (since or "daily").lower()
    if normalized == "weekly":
        return 7
    if normalized == "monthly":
        return 30
    return 1


async def _fetch_from_github_search(language: str, since: str, headers: dict[str, str]) -> dict:
    days = _since_days(since)
    start_date = (datetime.now(timezone.utc) - timedelta(days=days)).date().isoformat()

    query_parts = [f"created:>{start_date}"]
    if language:
        query_parts.append(f"language:{language}")

    query = " ".join(query_parts)
    params = {
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": 10,
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            "https://api.github.com/search/repositories",
            params=params,
            headers=headers,
        )
        resp.raise_for_status()
        raw = resp.json()

    items = raw.get("items", [])
    if not items:
        raise ValueError("GitHub search returned no repositories")

    repos = []
    for item in items[:10]:
        repos.append(
            {
                "name": item.get("full_name", ""),
                "description": (item.get("description") or "")[:120],
                "language": item.get("language") or "",
                "stars": item.get("stargazers_count", 0),
                "forks": item.get("forks_count", 0),
                "today_stars": None,
                "url": item.get("html_url", ""),
            }
        )

    repos = [repo for repo in repos if repo["name"]]
    if not repos:
        raise ValueError("GitHub search returned empty repository names")

    return {
        "type": "trending",
        "data": {
            "repos": repos,
            "language": language or "all",
            "since": since,
            "source": "github-search",
        },
    }


async def _fetch_trending_api(language: str, since: str) -> dict:
    """Fallback to an informal trending mirror when GitHub search is unavailable."""
    # This uses a community mirror of the trending page
    url = "https://api.gitterapp.com/repositories"
    params = {"language": language, "since": since}

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        raw = resp.json()

    if not isinstance(raw, list) or len(raw) == 0:
        raise ValueError("Trending API returned no repositories")

    repos = []
    for r in raw[:10]:
        repos.append({
            "name": r.get("fullName", r.get("name", "")),
            "description": (r.get("description", "") or "")[:100],
            "language": r.get("language", ""),
            "stars": r.get("stars", r.get("stargazers_count", 0)),
            "forks": r.get("forks", r.get("forks_count", 0)),
            "today_stars": r.get("currentPeriodStars", r.get("todayStars", 0)),
            "url": r.get("url", r.get("html_url", "")),
        })

    repos = [repo for repo in repos if repo["name"]]
    if not repos:
        raise ValueError("Trending API produced empty repository names")

    return {
        "type": "trending",
        "data": {
            "repos": repos,
            "language": language or "all",
            "since": since,
            "source": "gitterapp",
        },
    }
