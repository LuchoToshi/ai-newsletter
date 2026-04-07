from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional

import feedparser
import httpx
from dateutil import parser as dateutil_parser

from newsletter.config import (
    LOOKBACK_HOURS,
    MAX_ITEMS_PER_SOURCE,
    ARXIV_MAX_ITEMS,
    ARXIV_KEYWORDS,
    RSS_SOURCES,
)

USER_AGENT = "AINewsletterBot/1.0"


@dataclass
class RawItem:
    url: str
    title: str
    source: str
    category: str
    published: datetime
    summary: str = ""
    full_text: str = ""
    is_arxiv: bool = False


def _parse_date(entry: feedparser.FeedParserDict) -> Optional[datetime]:
    for attr in ("published_parsed", "updated_parsed"):
        t = getattr(entry, attr, None)
        if t:
            try:
                import time
                return datetime(*t[:6], tzinfo=timezone.utc)
            except Exception:
                pass
    for attr in ("published", "updated"):
        val = getattr(entry, attr, None)
        if val:
            try:
                dt = dateutil_parser.parse(val)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc)
            except Exception:
                pass
    return None


def _is_recent(dt: Optional[datetime]) -> bool:
    if dt is None:
        return True  # include items with no date rather than drop them
    cutoff = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)
    return dt >= cutoff


def _clean_html(text: str) -> str:
    return re.sub(r"<[^>]+>", " ", text).strip()


def _is_arxiv_relevant(text: str) -> bool:
    lower = text.lower()
    return any(kw in lower for kw in ARXIV_KEYWORDS)


def _parse_feed(content: bytes, source: dict) -> list[RawItem]:
    feed = feedparser.parse(content)
    is_arxiv = source.get("arxiv", False)
    limit = ARXIV_MAX_ITEMS if is_arxiv else MAX_ITEMS_PER_SOURCE
    items: list[RawItem] = []

    for entry in feed.entries:
        url = getattr(entry, "link", "") or ""
        if not url:
            continue

        title = _clean_html(getattr(entry, "title", "") or "")
        raw_summary = _clean_html(getattr(entry, "summary", "") or getattr(entry, "description", "") or "")
        published = _parse_date(entry)

        if not _is_recent(published):
            continue

        if is_arxiv and not _is_arxiv_relevant(title + " " + raw_summary):
            continue

        items.append(RawItem(
            url=url,
            title=title,
            source=source["name"],
            category=source["category"],
            published=published or datetime.now(timezone.utc),
            summary=raw_summary[:1000],
            is_arxiv=is_arxiv,
        ))

        if len(items) >= limit:
            break

    return items


async def _fetch_one(client: httpx.AsyncClient, source: dict) -> list[RawItem]:
    try:
        resp = await client.get(
            source["url"],
            headers={"User-Agent": USER_AGENT},
            follow_redirects=True,
            timeout=15,
        )
        resp.raise_for_status()
        return _parse_feed(resp.content, source)
    except Exception as exc:
        print(f"[rss] WARN: failed to fetch {source['name']}: {exc}")
        return []


async def fetch_all_rss(sources: list[dict] = RSS_SOURCES) -> list[RawItem]:
    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(*[_fetch_one(client, src) for src in sources])
    items = [item for batch in results for item in batch]
    print(f"[rss] Fetched {len(items)} items from {len(sources)} sources")
    return items
