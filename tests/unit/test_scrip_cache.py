"""Unit tests for the scrip-master CSV cache (TTL expires at midnight)."""

from datetime import date

from neo_api_client.utils import scrip_cache


class _StubDate:
    """Stand-in for the ``date`` class exposing a fixed ``today()``."""

    def __init__(self, today):
        self._today = today

    def today(self):
        return self._today


def test_read_returns_none_when_not_cached():
    assert scrip_cache.read_csv("nse_cm") is None


def test_write_then_read_same_day(monkeypatch):
    monkeypatch.setattr(scrip_cache, "date", _StubDate(date(2026, 7, 14)))
    scrip_cache.write_csv("nse_cm", b"hello")
    assert scrip_cache.read_csv("nse_cm") == b"hello"


def test_cache_is_per_segment():
    scrip_cache.write_csv("nse_cm", b"cm-data")
    scrip_cache.write_csv("nse_fo", b"fo-data")
    assert scrip_cache.read_csv("nse_cm") == b"cm-data"
    assert scrip_cache.read_csv("nse_fo") == b"fo-data"


def test_cache_expires_after_midnight(monkeypatch):
    """A cache entry from a previous day must not be served today (TTL)."""
    monkeypatch.setattr(scrip_cache, "date", _StubDate(date(2026, 7, 14)))
    scrip_cache.write_csv("nse_cm", b"day-one-data")
    assert scrip_cache.read_csv("nse_cm") == b"day-one-data"

    monkeypatch.setattr(scrip_cache, "date", _StubDate(date(2026, 7, 15)))
    assert scrip_cache.read_csv("nse_cm") is None


def test_write_removes_stale_files_from_previous_day(monkeypatch):
    monkeypatch.setattr(scrip_cache, "date", _StubDate(date(2026, 7, 14)))
    scrip_cache.write_csv("nse_cm", b"old")

    monkeypatch.setattr(scrip_cache, "date", _StubDate(date(2026, 7, 15)))
    scrip_cache.write_csv("nse_cm", b"new")

    cache_dir = scrip_cache._cache_dir()
    files = list(cache_dir.glob("nse_cm_*.csv"))
    assert len(files) == 1
    assert files[0].read_bytes() == b"new"


def test_write_twice_same_day_keeps_current_file(monkeypatch):
    """Writing again on the same day must not delete the file it just wrote."""
    monkeypatch.setattr(scrip_cache, "date", _StubDate(date(2026, 7, 14)))
    scrip_cache.write_csv("nse_cm", b"first")
    scrip_cache.write_csv("nse_cm", b"second")
    assert scrip_cache.read_csv("nse_cm") == b"second"


def test_env_override_changes_cache_dir(tmp_path, monkeypatch):
    custom = tmp_path / "custom_cache"
    monkeypatch.setenv("NEO_SCRIP_CACHE_DIR", str(custom))
    scrip_cache.write_csv("nse_cm", b"data")
    assert (custom / f"nse_cm_{date.today().isoformat()}.csv").exists()
