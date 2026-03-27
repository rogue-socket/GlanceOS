import httpx
import logging

logger = logging.getLogger("glanceos.trending")


async def fetch_github_trending(language: str = "", since: str = "daily") -> dict:
    """Fetch trending repos from GitHub. Uses the unofficial trending page scraper API."""

    try:
        return await _fetch_trending_api(language, since)
    except Exception:
        logger.debug("Trending API failed, using sample data")

    return {
        "type": "trending",
        "data": {
            "repos": _get_sample_trending(),
            "language": language or "all",
            "since": since,
            "source": "sample",
        },
    }


async def _fetch_trending_api(language: str, since: str) -> dict:
    """Use the GitHub trending informal JSON endpoint."""
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


def _get_sample_trending() -> list:
    return [
        {
            "name": "pocketbase/pocketbase",
            "description": "Open Source realtime backend in 1 file",
            "language": "Go",
            "stars": 42800,
            "forks": 2100,
            "today_stars": 385,
            "url": "https://github.com/pocketbase/pocketbase",
        },
        {
            "name": "anthropics/claude-code",
            "description": "An agentic coding tool from Anthropic",
            "language": "TypeScript",
            "stars": 28500,
            "forks": 1800,
            "today_stars": 620,
            "url": "https://github.com/anthropics/claude-code",
        },
        {
            "name": "fastapi/fastapi",
            "description": "High performance Python web framework",
            "language": "Python",
            "stars": 81200,
            "forks": 6900,
            "today_stars": 142,
            "url": "https://github.com/fastapi/fastapi",
        },
        {
            "name": "oven-sh/bun",
            "description": "Incredibly fast JavaScript runtime, bundler, transpiler",
            "language": "Zig",
            "stars": 76300,
            "forks": 2800,
            "today_stars": 98,
            "url": "https://github.com/oven-sh/bun",
        },
        {
            "name": "denoland/deno",
            "description": "A modern runtime for JavaScript and TypeScript",
            "language": "Rust",
            "stars": 98700,
            "forks": 5400,
            "today_stars": 76,
            "url": "https://github.com/denoland/deno",
        },
    ]
