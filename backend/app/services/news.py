from __future__ import annotations

import asyncio
import json
import logging
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from html import unescape
from urllib.parse import urlparse

import httpx

from app.config import get_settings

logger = logging.getLogger("glanceos.news")

FEEDS_BY_CATEGORY: dict[str, list[tuple[str, str]]] = {
    "technology": [
        ("hacker-news-frontpage", "https://hnrss.org/frontpage?count=20"),
        ("hacker-news-newest", "https://hnrss.org/newest?points=40&count=20"),
        (
            "google-tech",
            "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtVnVHZ0pWVXlnQVAB?hl=en-IN&gl=IN&ceid=IN:en",
        ),
    ],
    "sports": [
        (
            "google-sports",
            "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp1ZEdvU0FtVnVHZ0pWVXlnQVAB?hl=en-IN&gl=IN&ceid=IN:en",
        ),
    ],
    "world": [
        (
            "google-world",
            "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx1YlY4U0FtVnVHZ0pWVXlnQVAB?hl=en-IN&gl=IN&ceid=IN:en",
        ),
    ],
    "business": [
        (
            "google-business",
            "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFZxYUdjU0FtVnVHZ0pWVXlnQVAB?hl=en-IN&gl=IN&ceid=IN:en",
        ),
    ],
    "general": [
        ("hacker-news-frontpage", "https://hnrss.org/frontpage?count=20"),
        ("google-general", "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en"),
    ],
}

CLICKBAIT_PATTERNS = [
    r"\b(breaks the internet|goes viral|you won't believe|shocking|stuns|stunned)\b",
    r"\b(what happened next|watch now|must see|slams|blasts)\b",
]

DEFAULT_PUBLISHED = datetime.utcnow().isoformat()

MAX_ARTICLES = 8
MAX_CONTENT_WORDS = 220
MAX_FALLBACK_SUMMARY_WORDS = 48
CONTENT_FETCH_CONCURRENCY = 3

HTML_TAG_RE = re.compile(r"<[^>]+>")
SCRIPT_STYLE_RE = re.compile(r"<(script|style)[^>]*>.*?</\1>", flags=re.IGNORECASE | re.DOTALL)
META_DESCRIPTION_RE = re.compile(
    r"<meta[^>]+(?:name=[\"']description[\"']|property=[\"']og:description[\"'])[^>]+content=[\"']([^\"']+)[\"'][^>]*>",
    flags=re.IGNORECASE,
)
PARAGRAPH_RE = re.compile(r"<p[^>]*>(.*?)</p>", flags=re.IGNORECASE | re.DOTALL)


async def fetch_news(category: str = "technology") -> dict:
    """Fetch articles (HN-first for tech) and generate content-aware summaries."""
    selected_category = category if category in FEEDS_BY_CATEGORY else "general"
    feeds = FEEDS_BY_CATEGORY.get(selected_category, FEEDS_BY_CATEGORY["general"])

    try:
        articles = await _fetch_from_feeds(feeds)
    except Exception as exc:
        logger.debug("News fetch failed for %s: %s", selected_category, exc)
        return {
            "type": "news",
            "data": {
                "category": selected_category,
                "articles": [],
                "source": "+".join(source for source, _ in feeds),
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
                "source": "+".join(source for source, _ in feeds),
                "status": "unavailable",
                "reason": "No headlines received",
                "llm_enriched": False,
            },
        }

    articles = await _enrich_articles_with_content(articles)

    settings = get_settings()

    llm_enriched = False
    if settings.news_use_llm and settings.news_llm_api_key.strip():
        try:
            summary_items = await _summarize_with_llm(articles, selected_category, settings)
            llm_enriched = True
        except Exception as exc:
            logger.debug("LLM summarization failed: %s", exc)
            summary_items = [_fallback_summary_item(item) for item in articles]
    else:
        summary_items = [_fallback_summary_item(item) for item in articles]

    for article, summary_item in zip(articles, summary_items):
        article["crux"] = summary_item.get("crux") or _fallback_crux(article)
        article["summary"] = summary_item.get("summary") or _fallback_summary(article)

    return {
        "type": "news",
        "data": {
            "category": selected_category,
            "articles": articles,
            "source": "+".join(source for source, _ in feeds),
            "status": "ok",
            "llm_enriched": llm_enriched,
        },
    }


async def _fetch_from_feeds(feeds: list[tuple[str, str]]) -> list[dict]:
    merged: list[dict] = []
    seen: set[str] = set()

    async with httpx.AsyncClient(timeout=12.0, follow_redirects=True) as client:
        for source_name, rss_url in feeds:
            try:
                response = await client.get(rss_url)
                response.raise_for_status()
                merged.extend(_parse_rss_items(response.text, source_name, seen))
            except Exception as exc:
                logger.debug("RSS source %s failed: %s", source_name, exc)

            if len(merged) >= MAX_ARTICLES:
                break

    return merged[:MAX_ARTICLES]


def _parse_rss_items(xml_text: str, source_name: str, seen: set[str]) -> list[dict]:
    root = ET.fromstring(xml_text)
    items = root.findall("./channel/item")
    articles: list[dict] = []

    for item in items:
        raw_title = (item.findtext("title") or "").strip()
        title, inferred_source = _split_google_title(raw_title)
        url = (item.findtext("link") or "").strip()
        if not title:
            continue

        dedupe_key = _article_dedupe_key(title, url)
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)

        source = (item.findtext("source") or inferred_source or source_name).strip()
        published = (item.findtext("pubDate") or DEFAULT_PUBLISHED).strip()
        description = _clean_html(item.findtext("description") or "")

        articles.append(
            {
                "title": title,
                "source": source,
                "url": url,
                "published": published,
                "description": description,
                "content": "",
            }
        )

        if len(articles) >= MAX_ARTICLES:
            break

    return articles


def _article_dedupe_key(title: str, url: str) -> str:
    normalized_url = (url or "").strip().lower()
    normalized_title = re.sub(r"\s+", " ", (title or "").strip().lower())
    return normalized_url or normalized_title


async def _enrich_articles_with_content(articles: list[dict]) -> list[dict]:
    semaphore = asyncio.Semaphore(CONTENT_FETCH_CONCURRENCY)

    async with httpx.AsyncClient(timeout=9.0, follow_redirects=True) as client:
        tasks = [
            _enrich_single_article(article, client, semaphore)
            for article in articles
        ]
        await asyncio.gather(*tasks)

    return articles


async def _enrich_single_article(article: dict, client: httpx.AsyncClient, semaphore: asyncio.Semaphore) -> None:
    url = (article.get("url") or "").strip()
    if not url.startswith("http"):
        article["content"] = article.get("description", "")
        return

    host = (urlparse(url).hostname or "").lower()
    if "news.ycombinator.com" in host:
        article["content"] = article.get("description", "")
        return

    try:
        async with semaphore:
            resp = await client.get(
                url,
                headers={
                    "User-Agent": "GlanceOS/0.1 (+news-summary)",
                    "Accept": "text/html,application/xhtml+xml",
                },
            )
            resp.raise_for_status()
            article["content"] = _extract_content_text(resp.text) or article.get("description", "")
    except Exception:
        article["content"] = article.get("description", "")


def _extract_content_text(html: str) -> str:
    if not html:
        return ""

    stripped = SCRIPT_STYLE_RE.sub(" ", html)
    candidates: list[str] = []

    for match in META_DESCRIPTION_RE.findall(stripped):
        text = _clean_html(match)
        if text:
            candidates.append(text)

    for para in PARAGRAPH_RE.findall(stripped):
        text = _clean_html(para)
        if len(text.split()) >= 6:
            candidates.append(text)
        if len(candidates) >= 12:
            break

    combined = " ".join(candidates)
    combined = re.sub(r"\s+", " ", combined).strip()
    if not combined:
        fallback = _clean_html(HTML_TAG_RE.sub(" ", stripped))
        combined = fallback

    words = combined.split()
    if len(words) > MAX_CONTENT_WORDS:
        combined = " ".join(words[:MAX_CONTENT_WORDS])

    return combined


async def _summarize_with_llm(articles: list[dict], category: str, settings) -> list[dict]:
    provider = (settings.news_llm_provider or "gemini").strip().lower()
    if provider == "gemini":
        return await _summarize_with_gemini(articles, category, settings)

    return await _summarize_with_openai_compatible(articles, category, settings)


async def _summarize_with_openai_compatible(articles: list[dict], category: str, settings) -> list[dict]:
    payload_items = [
        {
            "index": i,
            "title": article.get("title", ""),
            "source": article.get("source", ""),
            "description": article.get("description", ""),
            "content": article.get("content", ""),
        }
        for i, article in enumerate(articles)
    ]

    prompt = (
        "For each item, produce two outputs from the article content: "
        "(1) crux: one factual sentence, max 18 words; "
        "(2) summary: 2 short sentences with concrete details from content. "
        "Rules: neutral, non-clickbait, no speculation, no hype words, no invented facts. "
        "Return strict JSON only as {\"items\":[{\"index\":0,\"crux\":\"...\",\"summary\":\"...\"}]}"
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

    by_index = {
        item.get("index"): {
            "crux": (item.get("crux") or "").strip(),
            "summary": (item.get("summary") or "").strip(),
        }
        for item in parsed
        if isinstance(item, dict)
    }
    results: list[dict] = []
    for i, article in enumerate(articles):
        candidate = by_index.get(i) or {}
        results.append(
            {
                "crux": candidate.get("crux") or _fallback_crux(article),
                "summary": candidate.get("summary") or _fallback_summary(article),
            }
        )

    return results


async def _summarize_with_gemini(articles: list[dict], category: str, settings) -> list[dict]:
    payload_items = [
        {
            "index": i,
            "title": article.get("title", ""),
            "source": article.get("source", ""),
            "description": article.get("description", ""),
            "content": article.get("content", ""),
        }
        for i, article in enumerate(articles)
    ]

    prompt = (
        "For each item, produce two outputs from the article content: "
        "(1) crux: one factual sentence, max 18 words; "
        "(2) summary: 2 short sentences with concrete details from content. "
        "Rules: neutral, non-clickbait, no speculation, no invented facts. "
        "Return strict JSON only as {\"items\":[{\"index\":0,\"crux\":\"...\",\"summary\":\"...\"}]}.\n"
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
    by_index = {
        item.get("index"): {
            "crux": (item.get("crux") or "").strip(),
            "summary": (item.get("summary") or "").strip(),
        }
        for item in parsed
        if isinstance(item, dict)
    }

    results: list[dict] = []
    for i, article in enumerate(articles):
        candidate = by_index.get(i) or {}
        results.append(
            {
                "crux": candidate.get("crux") or _fallback_crux(article),
                "summary": candidate.get("summary") or _fallback_summary(article),
            }
        )

    return results


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


def _fallback_summary(article: dict) -> str:
    content = (article.get("content") or "").strip()
    description = (article.get("description") or "").strip()
    title = (article.get("title") or "").strip()

    base = content or description or title
    base = re.sub(r"\s+", " ", base).strip()
    if not base:
        return "No summary available"

    words = base.split()
    if len(words) > MAX_FALLBACK_SUMMARY_WORDS:
        base = " ".join(words[:MAX_FALLBACK_SUMMARY_WORDS]).rstrip(".,;:") + "..."

    return base


def _fallback_summary_item(article: dict) -> dict:
    return {
        "crux": _fallback_crux(article),
        "summary": _fallback_summary(article),
    }


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
