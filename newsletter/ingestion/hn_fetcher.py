from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone

import httpx

from newsletter.config import HN_QUERIES, HN_MIN_POINTS
from newsletter.ingestion.rss_reader import RawItem

_ALGOLIA_URL = "https://hn.algolia.com/api/v1/search"
USER_AGENT = "AINewsletterBot/1.0"


async def _fetch_query(client: httpx.AsyncClient, query: str, since_ts: int) -> list[dict]:
    params = {
        "query": query,
        "tags": "story",
        "numericFilters": f"points>{HN_MIN_POINTS},created_at_i>{since_ts}",
        "hitsPerPage": 20,
    }
    try:
        resp = await client.get(
            _ALGOLIA_URL,
            params=params,
            headers={"User-Agent": USER_AGENT},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json().get("hits", [])
    except Exception as exc:
        print(f"[hn] WARN: query '{query}' failed: {exc}")
        return []


def _hit_to_raw_item(hit: dict) -> RawItem | None:
    # Use the linked URL (not the HN discussion page) as the canonical URL.
    # If no external URL (Ask HN, etc.), skip.
    url = hit.get("url") or ""
    if not url:
        return None

    title = hit.get("title") or ""
    created = hit.get("created_at_i")
    published = (
        datetime.fromtimestamp(created, tz=timezone.utc) if created else datetime.now(timezone.utc)
    )

    return RawItem(
        url=url,
        title=title,
        source="Hacker News",
        category="media",
        published=published,
        summary="",
    )


async def fetch_hn_stories() -> list[RawItem]:
    since_ts = int(time.time()) - 86400  # last 24h
    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(*[_fetch_query(client, q, since_ts) for q in HN_QUERIES])

    seen_ids: set[str] = set()
    items: list[RawItem] = []
    for hits in results:
        for hit in hits:
            story_id = hit.get("objectID") or ""
            if story_id in seen_ids:
                continue
            seen_ids.add(story_id)
            item = _hit_to_raw_item(hit)
            if item:
                items.append(item)

    print(f"[hn] Fetched {len(items)} unique stories")
    return items
