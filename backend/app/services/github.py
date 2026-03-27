import httpx
import logging
from datetime import datetime, timedelta

from app.config import get_settings

logger = logging.getLogger("glanceos.github")


async def fetch_github_events(username: str = "octocat") -> dict:
    """Fetch GitHub events. Falls back to sample data on failure."""
    settings = get_settings()
    headers = {}
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"

    try:
        url = f"https://api.github.com/users/{username}/events"
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers=headers, params={"per_page": 10})
            resp.raise_for_status()
            events = resp.json()

        return {
            "type": "github",
            "data": {
                "username": username,
                "events": [
                    {
                        "id": e["id"],
                        "type": e["type"],
                        "repo": e["repo"]["name"],
                        "created_at": e["created_at"],
                    }
                    for e in events[:10]
                ],
                "source": "live",
            },
        }
    except Exception:
        logger.debug("GitHub API failed, using sample data")

    return {
        "type": "github",
        "data": {
            "username": username,
            "events": _get_sample_events(username),
            "source": "sample",
        },
    }


def _get_sample_events(username: str) -> list:
    now = datetime.utcnow()
    return [
        {"id": "1", "type": "PushEvent", "repo": f"{username}/dotfiles", "created_at": (now - timedelta(minutes=12)).isoformat() + "Z"},
        {"id": "2", "type": "CreateEvent", "repo": f"{username}/new-project", "created_at": (now - timedelta(hours=1)).isoformat() + "Z"},
        {"id": "3", "type": "WatchEvent", "repo": "torvalds/linux", "created_at": (now - timedelta(hours=3)).isoformat() + "Z"},
        {"id": "4", "type": "PullRequestEvent", "repo": f"{username}/webapp", "created_at": (now - timedelta(hours=5)).isoformat() + "Z"},
        {"id": "5", "type": "IssueCommentEvent", "repo": "python/cpython", "created_at": (now - timedelta(hours=8)).isoformat() + "Z"},
    ]
