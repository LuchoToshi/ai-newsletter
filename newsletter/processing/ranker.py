from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from datetime import datetime

import anthropic

from newsletter.config import (
    CLAUDE_MODEL,
    CLAUDE_BATCH_SIZE,
    MAX_TOKENS_PER_BATCH,
    MIN_RELEVANCE_SCORE,
    TOP_N_FINAL,
)
from newsletter.ingestion.rss_reader import RawItem
from newsletter.processing.prompts import BATCH_SCORE_PROMPT, EDITORIAL_INTRO_PROMPT


@dataclass
class ScoredItem:
    url: str
    title: str
    source: str
    score: int
    summary: str
    why_it_matters: str
    category_tag: str
    published: datetime
    is_arxiv: bool = False


def _strip_code_fences(text: str) -> str:
    return re.sub(r"^```(?:json)?\n?|```$", "", text.strip(), flags=re.MULTILINE).strip()


def _call_with_retry(client: anthropic.Anthropic, **kwargs) -> str:
    delays = [2, 4, 8]
    last_exc: Exception | None = None
    for attempt, delay in enumerate(delays, 1):
        try:
            msg = client.messages.create(**kwargs)
            return msg.content[0].text
        except Exception as exc:
            last_exc = exc
            if attempt < len(delays):
                print(f"[ranker] Attempt {attempt} failed ({exc}), retrying in {delay}s...")
                time.sleep(delay)
    raise RuntimeError(f"Claude call failed after retries: {last_exc}") from last_exc


class NewsRanker:
    def __init__(self) -> None:
        self.client = anthropic.Anthropic()

    def score_and_summarize(self, items: list[RawItem]) -> list[ScoredItem]:
        batches = [items[i: i + CLAUDE_BATCH_SIZE] for i in range(0, len(items), CLAUDE_BATCH_SIZE)]
        scored: list[ScoredItem] = []

        for i, batch in enumerate(batches):
            print(f"[ranker] Scoring batch {i + 1}/{len(batches)} ({len(batch)} items)...")
            scored.extend(self._score_batch(batch))

        # Sort by score descending, deduplicate by URL, take top N
        seen_urls: set[str] = set()
        unique: list[ScoredItem] = []
        for item in sorted(scored, key=lambda x: x.score, reverse=True):
            if item.url not in seen_urls:
                seen_urls.add(item.url)
                unique.append(item)
            if len(unique) >= TOP_N_FINAL:
                break

        print(f"[ranker] {len(unique)} items passed threshold (score >= {MIN_RELEVANCE_SCORE})")
        return unique

    def _score_batch(self, batch: list[RawItem]) -> list[ScoredItem]:
        payload = [
            {
                "id": i,
                "title": item.title,
                "source": item.source,
                "category": item.category,
                "summary": (item.full_text or item.summary)[:800],
                "url": item.url,
            }
            for i, item in enumerate(batch)
        ]

        raw = _call_with_retry(
            self.client,
            model=CLAUDE_MODEL,
            max_tokens=MAX_TOKENS_PER_BATCH,
            messages=[{
                "role": "user",
                "content": BATCH_SCORE_PROMPT.format(items=json.dumps(payload, ensure_ascii=False)),
            }],
        )

        try:
            results = json.loads(_strip_code_fences(raw))
        except json.JSONDecodeError:
            # Retry once with explicit instruction
            print("[ranker] WARN: JSON parse failed, retrying with stricter prompt...")
            raw2 = _call_with_retry(
                self.client,
                model=CLAUDE_MODEL,
                max_tokens=MAX_TOKENS_PER_BATCH,
                messages=[
                    {"role": "user", "content": BATCH_SCORE_PROMPT.format(items=json.dumps(payload, ensure_ascii=False))},
                    {"role": "assistant", "content": raw},
                    {"role": "user", "content": "Your response was not valid JSON. Return ONLY a valid JSON array, nothing else."},
                ],
            )
            results = json.loads(_strip_code_fences(raw2))

        id_map = {i: item for i, item in enumerate(batch)}
        scored: list[ScoredItem] = []

        for r in results:
            score = int(r.get("score", 0))
            if score < MIN_RELEVANCE_SCORE:
                continue
            idx = int(r.get("id", -1))
            original = id_map.get(idx)
            if original is None:
                continue
            scored.append(ScoredItem(
                url=original.url,
                title=r.get("headline") or original.title,
                source=original.source,
                score=score,
                summary=r.get("summary") or "",
                why_it_matters=r.get("why_it_matters") or "",
                category_tag=r.get("category_tag") or "Industry Move",
                published=original.published,
                is_arxiv=original.is_arxiv,
            ))

        return scored

    def generate_intro(self, top_items: list[ScoredItem]) -> str:
        titles = "\n".join(f"- {item.title}" for item in top_items[:8])
        return _call_with_retry(
            self.client,
            model=CLAUDE_MODEL,
            max_tokens=300,
            messages=[{
                "role": "user",
                "content": EDITORIAL_INTRO_PROMPT.format(titles=titles),
            }],
        ).strip()
