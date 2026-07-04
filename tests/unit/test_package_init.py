"""Tests for the top-level ``neo_api_client`` package import behavior."""

import builtins
import importlib

import neo_api_client


def test_feed_symbols_exported_by_default():
    """With websockets installed (core dep), feed symbols are exported."""
    assert "SFeedWebSocket" in neo_api_client.__all__
    assert hasattr(neo_api_client, "SFeedWebSocket")
    assert hasattr(neo_api_client, "WsToken")


def test_import_fallback_when_websockets_missing(monkeypatch):
    """The `except ImportError` fallback keeps the SDK importable and drops the
    feed symbols from ``__all__`` when the WebSocket deps are unavailable.

    We simulate the missing dependency by making imports of the feed subpackage
    raise ImportError, then reload the package. The package is reloaded again in
    a finally block so the rest of the test session sees the normal state.
    """
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name.startswith("neo_api_client.websocket.feed"):
            raise ImportError("simulated missing websockets")
        return real_import(name, *args, **kwargs)

    try:
        monkeypatch.setattr(builtins, "__import__", fake_import)
        reloaded = importlib.reload(neo_api_client)

        # Fallback path taken: no feed symbols, but core API still present.
        assert reloaded.__all_feed__ == []
        assert "SFeedWebSocket" not in reloaded.__all__
        assert "NeoAPI" in reloaded.__all__
        assert hasattr(reloaded, "NeoAPI")
    finally:
        # Restore the real import machinery and reload cleanly for other tests.
        monkeypatch.undo()
        importlib.reload(neo_api_client)

    # Sanity: back to normal after restore.
    assert "SFeedWebSocket" in neo_api_client.__all__
