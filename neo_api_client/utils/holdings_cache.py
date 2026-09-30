"""File-based cache for a day's holdings() response, keyed by account (UCC).

positions() checks this before deciding whether it needs to fetch holdings()
itself (see NeoAPI._get_cached_holdings_by_identifier()). An in-memory-only
cache doesn't survive across separate process runs -- e.g. running
smoke_test.py twice in a row -- so this persists it to disk instead, valid
until midnight local time. Scoped per UCC since holdings are private,
per-account data and the cache directory is shared machine-wide.
"""

import json
import os
from datetime import date
from pathlib import Path
from typing import Any

_DEFAULT_CACHE_DIR = Path.home() / ".kotak_neo" / "holdings_cache"


def _cache_dir() -> Path:
    override = os.environ.get("NEO_HOLDINGS_CACHE_DIR")
    return Path(override) if override else _DEFAULT_CACHE_DIR


def _cache_path(ucc: str, day: date) -> Path:
    return _cache_dir() / f"{ucc}_{day.isoformat()}.json"


def read_holdings(ucc: str | None) -> dict[str, Any] | None:
    """Return today's cached holdings-by-identifier dict for this account,
    or None if not cached (or the cache file is missing/corrupt)."""
    if not ucc:
        return None
    path = _cache_path(ucc, date.today())
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def write_holdings(ucc: str | None, holdings_by_identifier: dict[str, Any]) -> None:
    """Cache today's holdings-by-identifier dict for this account; valid
    until midnight.

    Also removes any stale cache file(s) left over from a previous day for
    this account, so the cache directory doesn't grow unbounded.
    """
    if not ucc:
        return
    cache_dir = _cache_dir()
    cache_dir.mkdir(parents=True, exist_ok=True)

    today_path = _cache_path(ucc, date.today())
    for stale in cache_dir.glob(f"{ucc}_*.json"):
        if stale != today_path:
            stale.unlink(missing_ok=True)

    today_path.write_text(json.dumps(holdings_by_identifier))
