import httpx
from app.config import get_settings


async def fetch_github_events(username: str = "octocat") -> dict:
    settings = get_settings()
    headers = {}
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"

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
        },
    }
