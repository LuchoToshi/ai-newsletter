from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse, urlunparse, urlencode, parse_qsl


class SeenURLStore:
    def __init__(self, path: str = "data/seen_urls.json"):
        self.path = Path(path)
        self._seen: dict[str, str] = self._load()

    def _load(self) -> dict[str, str]:
        if not self.path.exists():
            return {}
        try:
            raw = json.loads(self.path.read_text())
        except (json.JSONDecodeError, OSError):
            return {}

        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        return {
            url: ts
            for url, ts in raw.items()
            if datetime.fromisoformat(ts) > cutoff
        }

    def is_new(self, url: str) -> bool:
        return self._normalize(url) not in self._seen

    def mark_seen(self, urls: list[str]) -> None:
        now = datetime.now(timezone.utc).isoformat()
        for url in urls:
            self._seen[self._normalize(url)] = now
        self._save()

    def _normalize(self, url: str) -> str:
        try:
            parsed = urlparse(url)
            # Strip utm_* and other tracking params
            clean_params = [(k, v) for k, v in parse_qsl(parsed.query) if not k.startswith("utm_")]
            clean_query = urlencode(clean_params)
            normalized = urlunparse(parsed._replace(
                scheme="https",
                query=clean_query,
                fragment="",
            ))
            return normalized.rstrip("/")
        except Exception:
            return url.rstrip("/")

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._seen, indent=2))
