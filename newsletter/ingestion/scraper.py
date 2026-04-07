from __future__ import annotations

import asyncio
import re

import httpx

from newsletter.ingestion.rss_reader import RawItem

USER_AGENT = "AINewsletterBot/1.0"
MAX_FULL_TEXT = 1500
ENRICH_SUMMARY_THRESHOLD = 150  # enrich if summary shorter than this


def _extract_body(html: str) -> str:
    # Try <article> first, then <main>, then fall back to full body
    for tag in ("article", "main", "body"):
        match = re.search(rf"<{tag}[^>]*>(.*?)</{tag}>", html, re.DOTALL | re.IGNORECASE)
        if match:
            text = re.sub(r"<[^>]+>", " ", match.group(1))
            text = re.sub(r"\s+", " ", text).strip()
            return text[:MAX_FULL_TEXT]
    return ""


async def _enrich_one(client: httpx.AsyncClient, item: RawItem) -> RawItem:
    # ArXiv: summary from RSS is the abstract — sufficient, skip HTTP fetch
    if item.is_arxiv:
        return item
    # Already has enough text
    if len(item.summary) >= ENRICH_SUMMARY_THRESHOLD:
        return item
    # Skip PDFs
    if item.url.lower().endswith(".pdf"):
        return item

    try:
        resp = await client.get(
            item.url,
            headers={"User-Agent": USER_AGENT},
            follow_redirects=True,
            timeout=12,
        )
        resp.raise_for_status()
        body = _extract_body(resp.text)
        if body:
            item.full_text = body
    except Exception as exc:
        print(f"[scraper] WARN: could not enrich {item.url[:60]}: {exc}")

    return item


async def enrich_items(items: list[RawItem]) -> list[RawItem]:
    needs_enrichment = [item for item in items if len(item.summary) < ENRICH_SUMMARY_THRESHOLD and not item.is_arxiv]
    already_ok = [item for item in items if item not in needs_enrichment]

    if not needs_enrichment:
        return items

    async with httpx.AsyncClient() as client:
        enriched = await asyncio.gather(*[_enrich_one(client, item) for item in needs_enrichment])

    print(f"[scraper] Enriched {len(needs_enrichment)} thin-summary items")
    return already_ok + list(enriched)
