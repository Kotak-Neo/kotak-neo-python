"""File-based cache for downloaded scrip-master CSV files.

Kotak publishes a fresh scrip-master CSV roughly once a day. ``search_scrip()``
otherwise re-fetches the (large) CSV for the requested exchange segment on
every call. This cache keeps the downloaded bytes on disk for the rest of the
calendar day they were fetched — a TTL that expires at midnight local time —
so repeat searches on the same day reuse the cached file instead of hitting
the network again.
"""

import os
from datetime import date
from pathlib import Path

_DEFAULT_CACHE_DIR = Path.home() / ".kotak_neo" / "scrip_cache"


def _cache_dir():
    override = os.environ.get("NEO_SCRIP_CACHE_DIR")
    return Path(override) if override else _DEFAULT_CACHE_DIR


def _cache_path(exchange_segment, day):
    return _cache_dir() / f"{exchange_segment}_{day.isoformat()}.csv"


def read_csv(exchange_segment):
    """Return today's cached CSV bytes for this segment, or None if not cached."""
    path = _cache_path(exchange_segment, date.today())
    if path.exists():
        return path.read_bytes()
    return None


def write_csv(exchange_segment, content):
    """Cache today's CSV bytes for this segment; valid until midnight.

    Also removes any stale cache file(s) left over from a previous day for
    this segment, so the cache directory doesn't grow unbounded.
    """
    cache_dir = _cache_dir()
    cache_dir.mkdir(parents=True, exist_ok=True)

    today_path = _cache_path(exchange_segment, date.today())
    for stale in cache_dir.glob(f"{exchange_segment}_*.csv"):
        if stale != today_path:
            stale.unlink(missing_ok=True)

    today_path.write_bytes(content)
