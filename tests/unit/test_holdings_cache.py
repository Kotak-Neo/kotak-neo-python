"""Unit tests for the on-disk holdings() cache (TTL expires at midnight, scoped per UCC)."""

from datetime import date

from neo_api_client.utils import holdings_cache


class _StubDate:
    """Stand-in for the ``date`` class exposing a fixed ``today()``."""

    def __init__(self, today):
        self._today = today

    def today(self):
        return self._today


def test_read_returns_none_when_not_cached():
    assert holdings_cache.read_holdings("UCC1") is None


def test_read_returns_none_without_a_ucc():
    holdings_cache.write_holdings(None, {"61304": {"averagePrice": 100.0}})
    assert holdings_cache.read_holdings(None) is None
    assert holdings_cache.read_holdings("") is None


def test_write_then_read_same_day(monkeypatch):
    monkeypatch.setattr(holdings_cache, "date", _StubDate(date(2026, 7, 14)))
    holdings_cache.write_holdings("UCC1", {"61304": {"averagePrice": 100.0}})
    assert holdings_cache.read_holdings("UCC1") == {"61304": {"averagePrice": 100.0}}


def test_cache_is_per_ucc():
    holdings_cache.write_holdings("UCC1", {"61304": {"averagePrice": 100.0}})
    holdings_cache.write_holdings("UCC2", {"61305": {"averagePrice": 200.0}})
    assert holdings_cache.read_holdings("UCC1") == {"61304": {"averagePrice": 100.0}}
    assert holdings_cache.read_holdings("UCC2") == {"61305": {"averagePrice": 200.0}}


def test_cache_expires_after_midnight(monkeypatch):
    """A cache entry from a previous day must not be served today (TTL)."""
    monkeypatch.setattr(holdings_cache, "date", _StubDate(date(2026, 7, 14)))
    holdings_cache.write_holdings("UCC1", {"61304": {"averagePrice": 100.0}})
    assert holdings_cache.read_holdings("UCC1") is not None

    monkeypatch.setattr(holdings_cache, "date", _StubDate(date(2026, 7, 15)))
    assert holdings_cache.read_holdings("UCC1") is None


def test_write_removes_stale_files_from_previous_day(monkeypatch):
    monkeypatch.setattr(holdings_cache, "date", _StubDate(date(2026, 7, 14)))
    holdings_cache.write_holdings("UCC1", {"61304": {"averagePrice": 100.0}})

    monkeypatch.setattr(holdings_cache, "date", _StubDate(date(2026, 7, 15)))
    holdings_cache.write_holdings("UCC1", {"61304": {"averagePrice": 200.0}})

    cache_dir = holdings_cache._cache_dir()
    files = list(cache_dir.glob("UCC1_*.json"))
    assert len(files) == 1
    assert holdings_cache.read_holdings("UCC1") == {"61304": {"averagePrice": 200.0}}


def test_read_returns_none_for_corrupt_cache_file():
    cache_dir = holdings_cache._cache_dir()
    cache_dir.mkdir(parents=True, exist_ok=True)
    (cache_dir / f"UCC1_{date.today().isoformat()}.json").write_text("not json")

    assert holdings_cache.read_holdings("UCC1") is None


def test_env_override_changes_cache_dir(tmp_path, monkeypatch):
    custom = tmp_path / "custom_holdings_cache"
    monkeypatch.setenv("NEO_HOLDINGS_CACHE_DIR", str(custom))
    holdings_cache.write_holdings("UCC1", {"61304": {"averagePrice": 100.0}})
    assert (custom / f"UCC1_{date.today().isoformat()}.json").exists()
