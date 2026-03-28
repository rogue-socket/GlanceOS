import httpx
import logging
import re
from datetime import datetime, timedelta, timezone
from html import unescape
from urllib.parse import quote

from app.config import get_settings

logger = logging.getLogger("glanceos.trending")

TRENDING_ITEM_RE = re.compile(r'<article[^>]*class="[^"]*Box-row[^"]*"[^>]*>(.*?)</article>', re.DOTALL)
TRENDING_REPO_RE = re.compile(r'href="/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)"')
TRENDING_DESC_RE = re.compile(r"<p[^>]*>(.*?)</p>", re.DOTALL)


def _clean_html(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", value or "")
    text = unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _parse_int(value: str) -> int:
    digits = re.sub(r"[^0-9]", "", value or "")
    if not digits:
        return 0
    try:
        return int(digits)
    except ValueError:
        return 0


def _extract_anchor_metric(block: str, repo_name: str, suffix: str) -> int:
    pattern = rf'href="/{re.escape(repo_name)}{suffix}"[^>]*>(.*?)</a>'
    match = re.search(pattern, block, flags=re.DOTALL)
    if not match:
        return 0
    return _parse_int(_clean_html(match.group(1)))


def _extract_today_stars(block: str) -> int:
    match = re.search(r"([0-9][0-9,]*)\s+stars?\s+today", _clean_html(block), flags=re.IGNORECASE)
    if not match:
        return 0
    return _parse_int(match.group(1))


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
    except httpx.HTTPStatusError as exc:
        if "Authorization" in headers and exc.response.status_code in {401, 403}:
            logger.warning("Trending auth failed (status=%s), retrying without token", exc.response.status_code)
            retry_headers = dict(headers)
            retry_headers.pop("Authorization", None)
            try:
                return await _fetch_from_github_search(language, since, retry_headers)
            except Exception as retry_exc:
                logger.warning("Trending retry without token failed: %s", retry_exc)
        else:
            logger.warning("Trending fetch failed: %s", exc)
    except Exception as exc:
        logger.warning("Trending fetch failed: %s", exc)

    try:
        return await _fetch_from_github_trending_html(language, since)
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


async def _fetch_from_github_trending_html(language: str, since: str) -> dict:
    normalized_since = (since or "daily").lower()
    if normalized_since not in {"daily", "weekly", "monthly"}:
        normalized_since = "daily"

    base_url = "https://github.com/trending"
    trending_url = f"{base_url}/{quote(language)}" if language else base_url

    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        resp = await client.get(
            trending_url,
            params={"since": normalized_since},
            headers={"User-Agent": "GlanceOS/0.1", "Accept": "text/html"},
        )
        resp.raise_for_status()
        html = resp.text

    blocks = TRENDING_ITEM_RE.findall(html)
    if not blocks:
        raise ValueError("GitHub trending HTML returned no repository blocks")

    repos: list[dict] = []
    for block in blocks:
        repo_match = TRENDING_REPO_RE.search(block)
        if not repo_match:
            continue

        name = repo_match.group(1).strip()
        desc_match = TRENDING_DESC_RE.search(block)
        description = _clean_html(desc_match.group(1))[:120] if desc_match else ""

        lang_match = re.search(r'itemprop="programmingLanguage"[^>]*>([^<]+)<', block)
        language_name = _clean_html(lang_match.group(1)) if lang_match else ""

        stars = _extract_anchor_metric(block, name, "/stargazers")
        forks = _extract_anchor_metric(block, name, "/forks")
        today_stars = _extract_today_stars(block)

        repos.append(
            {
                "name": name,
                "description": description,
                "language": language_name,
                "stars": stars,
                "forks": forks,
                "today_stars": today_stars,
                "url": f"https://github.com/{name}",
            }
        )

        if len(repos) >= 10:
            break

    if not repos:
        raise ValueError("GitHub trending HTML parsing produced no repositories")

    return {
        "type": "trending",
        "data": {
            "repos": repos,
            "language": language or "all",
            "since": normalized_since,
            "source": "github-trending-html",
        },
    }
