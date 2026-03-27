import httpx
import logging
from datetime import datetime

logger = logging.getLogger("glanceos.news")


async def fetch_news(category: str = "technology") -> dict:
    """Fetch headlines. Tries free RSS-to-JSON services, falls back to samples."""

    try:
        return await _fetch_from_rss(category)
    except Exception:
        logger.debug("RSS fetch failed, using sample data")

    return {
        "type": "news",
        "data": {
            "category": category,
            "articles": _get_sample_articles(),
            "source": "sample",
        },
    }


async def _fetch_from_rss(category: str) -> dict:
    """Use rss2json.com (free, no key required) to parse Google News RSS."""
    feeds = {
        "technology": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtVnVHZ0pWVXlnQVAB",
        "sports": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp1ZEdvU0FtVnVHZ0pWVXlnQVAB",
        "world": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx1YlY4U0FtVnVHZ0pWVXlnQVAB",
        "general": "https://news.google.com/rss",
    }
    rss_url = feeds.get(category, feeds["general"])
    api_url = "https://api.rss2json.com/v1/api.json"

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(api_url, params={"rss_url": rss_url})
        resp.raise_for_status()
        raw = resp.json()

    articles = []
    for item in raw.get("items", [])[:8]:
        articles.append({
            "title": item.get("title", ""),
            "source": item.get("author", item.get("source", "")),
            "url": item.get("link", ""),
            "published": item.get("pubDate", ""),
        })

    return {
        "type": "news",
        "data": {
            "category": category,
            "articles": articles,
            "source": "google-rss",
        },
    }


def _get_sample_articles() -> list:
    return [
        {
            "title": "Raspberry Pi 6 Announced with 16GB RAM",
            "source": "TechCrunch",
            "url": "",
            "published": datetime.utcnow().isoformat(),
        },
        {
            "title": "Open Source AI Models Surpass GPT-4 on New Benchmarks",
            "source": "Ars Technica",
            "url": "",
            "published": datetime.utcnow().isoformat(),
        },
        {
            "title": "SpaceX Starship Completes 10th Successful Landing",
            "source": "Reuters",
            "url": "",
            "published": datetime.utcnow().isoformat(),
        },
        {
            "title": "India's UPI Crosses 20 Billion Monthly Transactions",
            "source": "Economic Times",
            "url": "",
            "published": datetime.utcnow().isoformat(),
        },
        {
            "title": "Linux 7.0 Kernel Released with Major Performance Gains",
            "source": "Phoronix",
            "url": "",
            "published": datetime.utcnow().isoformat(),
        },
    ]
