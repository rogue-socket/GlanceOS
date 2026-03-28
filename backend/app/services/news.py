from __future__ import annotations

import json
import logging
import re
import xml.etree.ElementTree as ET
from html import unescape

import httpx

from app.config import get_settings

logger = logging.getLogger("glanceos.news")

GOOGLE_RSS_FEEDS: dict[str, str] = {
    "technology": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtVnVHZ0pWVXlnQVAB?hl=en-IN&gl=IN&ceid=IN:en",
    "sports": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp1ZEdvU0FtVnVHZ0pWVXlnQVAB?hl=en-IN&gl=IN&ceid=IN:en",
    "world": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx1YlY4U0FtVnVHZ0pWVXlnQVAB?hl=en-IN&gl=IN&ceid=IN:en",
    "business": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFZxYUdjU0FtVnVHZ0pWVXlnQVAB?hl=en-IN&gl=IN&ceid=IN:en",
    "general": "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en",
}

CLICKBAIT_PATTERNS = [
    r"\b(breaks the internet|goes viral|you won't believe|shocking|stuns|stunned)\b",
    r"\b(what happened next|watch now|must see|slams|blasts)\b",
]


async def fetch_news(category: str = "technology") -> dict:
    """Fetch real news articles and generate concise, less-clickbait crux lines."""
    selected_category = category if category in GOOGLE_RSS_FEEDS else "general"

    try:
        articles = await _fetch_from_google_rss(selected_category)
    except Exception as exc:
        logger.debug("News fetch failed for %s: %s", selected_category, exc)
        return {
            "type": "news",
            "data": {
                "category": selected_category,
                "articles": [],
                "source": "google-rss",
                "status": "unavailable",
                "reason": "Live news unavailable",
                "llm_enriched": False,
            },
        }

    if not articles:
        return {
            "type": "news",
            "data": {
                "category": selected_category,
                "articles": [],
                "source": "google-rss",
                "status": "unavailable",
                "reason": "No headlines received",
                "llm_enriched": False,
            },
        }

    settings = get_settings()

    llm_enriched = False
    if settings.news_use_llm and settings.news_llm_api_key.strip():
        try:
            crux_list = await _summarize_with_llm(articles, selected_category, settings)
            llm_enriched = True
        except Exception as exc:
            logger.debug("LLM summarization failed: %s", exc)
            crux_list = [_fallback_crux(item) for item in articles]
    else:
        crux_list = [_fallback_crux(item) for item in articles]

    for article, crux in zip(articles, crux_list):
        article["crux"] = crux

    return {
        "type": "news",
        "data": {
            "category": selected_category,
            "articles": articles,
            "source": "google-rss",
            "status": "ok",
            "llm_enriched": llm_enriched,
        },
    }


async def _fetch_from_google_rss(category: str) -> list[dict]:
    rss_url = GOOGLE_RSS_FEEDS.get(category, GOOGLE_RSS_FEEDS["general"])

    async with httpx.AsyncClient(timeout=12.0, follow_redirects=True) as client:
        response = await client.get(rss_url)
        response.raise_for_status()
        xml_text = response.text

    root = ET.fromstring(xml_text)
    items = root.findall("./channel/item")

    articles: list[dict] = []
    for item in items[:8]:
        raw_title = (item.findtext("title") or "").strip()
        title, inferred_source = _split_google_title(raw_title)
        source = (item.findtext("source") or inferred_source or "Google News").strip()
        url = (item.findtext("link") or "").strip()
        published = (item.findtext("pubDate") or "").strip()
        description = _clean_html(item.findtext("description") or "")

        if not title:
            continue

        articles.append(
            {
                "title": title,
                "source": source,
                "url": url,
                "published": published,
                "description": description,
            }
        )

    return articles


async def _summarize_with_llm(articles: list[dict], category: str, settings) -> list[str]:
    provider = (settings.news_llm_provider or "gemini").strip().lower()
    if provider == "gemini":
        return await _summarize_with_gemini(articles, category, settings)

    return await _summarize_with_openai_compatible(articles, category, settings)


async def _summarize_with_openai_compatible(articles: list[dict], category: str, settings) -> list[str]:
    payload_items = [
        {
            "index": i,
            "title": article.get("title", ""),
            "source": article.get("source", ""),
            "description": article.get("description", ""),
        }
        for i, article in enumerate(articles)
    ]

    prompt = (
        "Rewrite each news item into one concise factual crux sentence. "
        "Rules: neutral tone, no clickbait words, no speculation, max 18 words, preserve key facts. "
        "Return strict JSON only as {\"items\":[{\"index\":0,\"crux\":\"...\"}]}."
    )

    request_body = {
        "model": settings.news_llm_model,
        "temperature": 0.2,
        "messages": [
            {
                "role": "system",
                "content": "You normalize headlines into concise factual summaries.",
            },
            {
                "role": "user",
                "content": f"Category: {category}\nItems: {json.dumps(payload_items, ensure_ascii=True)}\n{prompt}",
            },
        ],
    }

    headers = {
        "Authorization": f"Bearer {settings.news_llm_api_key}",
        "Content-Type": "application/json",
    }

    endpoint = settings.news_llm_base_url.rstrip("/") + "/chat/completions"
    async with httpx.AsyncClient(timeout=settings.news_llm_timeout_seconds) as client:
        response = await client.post(endpoint, json=request_body, headers=headers)
        response.raise_for_status()
        body = response.json()

    content = (
        body.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "")
    )
    parsed = _extract_llm_items(content)

    by_index = {item.get("index"): item.get("crux", "") for item in parsed}
    summaries = []
    for i, article in enumerate(articles):
        crux = (by_index.get(i) or "").strip()
        summaries.append(crux or _fallback_crux(article))

    return summaries


async def _summarize_with_gemini(articles: list[dict], category: str, settings) -> list[str]:
    payload_items = [
        {
            "index": i,
            "title": article.get("title", ""),
            "source": article.get("source", ""),
            "description": article.get("description", ""),
        }
        for i, article in enumerate(articles)
    ]

    prompt = (
        "Rewrite each news item into one concise factual crux sentence. "
        "Rules: neutral tone, no clickbait words, no speculation, max 18 words, preserve key facts. "
        "Return strict JSON only as {\"items\":[{\"index\":0,\"crux\":\"...\"}]}.\n"
        f"Category: {category}\nItems: {json.dumps(payload_items, ensure_ascii=True)}"
    )

    endpoint = (
        f"{settings.news_llm_base_url.rstrip('/')}/models/{settings.news_llm_model}:generateContent"
    )

    request_body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json",
        },
    }

    async with httpx.AsyncClient(timeout=settings.news_llm_timeout_seconds) as client:
        response = await client.post(
            endpoint,
            params={"key": settings.news_llm_api_key},
            json=request_body,
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        body = response.json()

    candidate_parts = (
        body.get("candidates", [{}])[0]
        .get("content", {})
        .get("parts", [])
    )
    content = "\n".join(
        str(part.get("text", "")) for part in candidate_parts if isinstance(part, dict)
    )

    parsed = _extract_llm_items(content)
    by_index = {item.get("index"): item.get("crux", "") for item in parsed}

    summaries = []
    for i, article in enumerate(articles):
        crux = (by_index.get(i) or "").strip()
        summaries.append(crux or _fallback_crux(article))

    return summaries


def _extract_llm_items(raw_text: str) -> list[dict]:
    if not raw_text:
        return []

    raw_text = raw_text.strip()
    if raw_text.startswith("```"):
        raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
        raw_text = re.sub(r"\s*```$", "", raw_text)

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw_text, flags=re.DOTALL)
        if not match:
            return []
        try:
            parsed = json.loads(match.group(0))
        except json.JSONDecodeError:
            return []

    if isinstance(parsed, list):
        return [item for item in parsed if isinstance(item, dict)]
    if isinstance(parsed, dict):
        items = parsed.get("items", [])
        if isinstance(items, list):
            return [item for item in items if isinstance(item, dict)]
    return []


def _fallback_crux(article: dict) -> str:
    title = (article.get("title") or "").strip()
    description = (article.get("description") or "").strip()

    for pattern in CLICKBAIT_PATTERNS:
        title = re.sub(pattern, "", title, flags=re.IGNORECASE)

    title = re.sub(r"\s+", " ", title).strip(" -:;,.!?")

    candidate = description if len(description.split()) >= 8 else title
    candidate = re.sub(r"\s+", " ", candidate).strip()
    if not candidate:
        return "No summary available"

    words = candidate.split()
    if len(words) > 18:
        candidate = " ".join(words[:18]).rstrip(".,;:") + "..."

    return candidate


def _split_google_title(raw_title: str) -> tuple[str, str]:
    title = (raw_title or "").strip()
    if not title:
        return "", ""

    if " - " in title:
        left, right = title.rsplit(" - ", 1)
        if left and right and len(right.split()) <= 5:
            return left.strip(), right.strip()

    return title, ""


def _clean_html(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", value or "")
    text = unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text
