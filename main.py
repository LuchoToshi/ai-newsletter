#!/usr/bin/env python3
"""
main.py — Daily AI Newsletter pipeline orchestrator.

Flags:
  --dry-run     Ingest and score items, print results, do NOT send email.
  --skip-send   Run the full pipeline but skip the final Resend call (useful for template testing).
  --save-html   Write the rendered email to /tmp/newsletter_preview.html for inspection.
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

if os.path.exists(".env"):
    from dotenv import load_dotenv
    load_dotenv(override=True)

from newsletter.config import RSS_SOURCES
from newsletter.ingestion.rss_reader import fetch_all_rss
from newsletter.ingestion.hn_fetcher import fetch_hn_stories
from newsletter.ingestion.scraper import enrich_items
from newsletter.ingestion.dedup import SeenURLStore
from newsletter.processing.ranker import NewsRanker
from newsletter.rendering.template import build_email_html, build_plain_text, build_subject
from newsletter.rendering.delivery.resend_sender import ResendSender


async def run(dry_run: bool, skip_send: bool, save_html: bool) -> None:
    date_str = datetime.now(timezone.utc).strftime("%B %d, %Y")
    print(f"\n{'='*50}")
    print(f"  Signal AI Newsletter — {date_str}")
    print(f"{'='*50}\n")

    # ── Step 1: Ingest ───────────────────────────────────────────────────────
    store = SeenURLStore("data/seen_urls.json")
    rss_items, hn_items = await asyncio.gather(
        fetch_all_rss(RSS_SOURCES),
        fetch_hn_stories(),
    )
    all_raw = rss_items + hn_items
    print(f"\n[pipeline] Total raw items: {len(all_raw)}")

    # ── Step 2: Dedup ────────────────────────────────────────────────────────
    new_items = [item for item in all_raw if store.is_new(item.url)]
    print(f"[pipeline] New after dedup: {len(new_items)}")

    if len(new_items) < 3:
        print("[pipeline] WARN: Fewer than 3 new items found. Skipping this run.")
        return

    # ── Step 3: Enrich ───────────────────────────────────────────────────────
    enriched = await enrich_items(new_items)

    # ── Step 4: Rank ─────────────────────────────────────────────────────────
    ranker = NewsRanker()
    top_items = ranker.score_and_summarize(enriched)

    if not top_items:
        print("[pipeline] WARN: No items passed the relevance threshold. Skipping send.")
        return

    if dry_run:
        print("\n[dry-run] Scored items:")
        for i, item in enumerate(top_items, 1):
            print(f"  {i:2}. [{item.score:2}] [{item.category_tag[:20]:20}] {item.title[:70]}")
        print("\n[dry-run] Done. No email sent.")
        return

    intro = ranker.generate_intro(top_items)

    # ── Step 5: Render ───────────────────────────────────────────────────────
    html = build_email_html(top_items, intro, date_str)
    plain = build_plain_text(top_items, intro, date_str)
    subject = build_subject(top_items, date_str)

    if save_html:
        preview_path = Path("/tmp/newsletter_preview.html")
        preview_path.write_text(html)
        print(f"[pipeline] HTML saved to {preview_path}")

    # ── Step 6: Send ─────────────────────────────────────────────────────────
    if not skip_send:
        sender = ResendSender()
        sender.send(subject=subject, html=html, plain_text=plain)
    else:
        print(f"[pipeline] Subject: {subject}")
        print("[pipeline] --skip-send set, email not sent.")

    # ── Step 7: Mark seen ────────────────────────────────────────────────────
    store.mark_seen([item.url for item in new_items])
    print(f"[pipeline] Marked {len(new_items)} URLs as seen.")
    print("\n[pipeline] Done.\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Signal AI Newsletter pipeline")
    parser.add_argument("--dry-run", action="store_true", help="Ingest + score only, no email")
    parser.add_argument("--skip-send", action="store_true", help="Full pipeline, skip email send")
    parser.add_argument("--save-html", action="store_true", help="Write HTML to /tmp/newsletter_preview.html")
    args = parser.parse_args()

    asyncio.run(run(
        dry_run=args.dry_run,
        skip_send=args.skip_send,
        save_html=args.save_html,
    ))


if __name__ == "__main__":
    main()
