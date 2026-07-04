"""End-to-end lifecycle coverage for SFeedWebSocket.

Drives connect() -> authenticate -> receive-loop -> subscribe -> close using a
scripted fake async WebSocket injected in place of ``websockets.connect``.
"""

import asyncio
import json
import struct

import pytest

pytest.importorskip("websockets")

from neo_api_client.websocket import feed as feed_module  # noqa: E402
from neo_api_client.websocket.feed import SFeedWebSocket, WsToken  # noqa: E402
from neo_api_client.websocket.feed import client as _client_mod  # noqa: E402
from neo_api_client.websocket.feed.protocol import (  # noqa: E402
    HEADER_SIZE,
    MSG_MARKET_OPEN,
)

_AUTH_OK = json.dumps(
    {
        "message_code": 1119,
        "format": "native_batch",
        "exchanges": {"nse_cm": {"value": 1, "divider": 100}},
    }
)


def _market_status_frame():
    return struct.Struct("<HHbBBBB").pack(HEADER_SIZE, MSG_MARKET_OPEN, 1, 0, 0, 0, 0)


class FakeAsyncWS:
    """Scripted async WebSocket. ``incoming`` is a list of frames recv() yields;
    once exhausted, recv() blocks (simulating an idle live feed)."""

    def __init__(self, incoming):
        self.sent = []
        self._incoming = list(incoming)
        self.state = type("S", (), {"name": "OPEN"})()
        self.closed = False

    async def send(self, data):
        self.sent.append(data)

    async def recv(self):
        if self._incoming:
            return self._incoming.pop(0)
        # No more scripted frames: block until cancelled (idle feed).
        await asyncio.sleep(3600)

    async def close(self):
        self.closed = True
        self.state = type("S", (), {"name": "CLOSED"})()


def _patch_connect(monkeypatch, fake):
    async def fake_connect(url, **kwargs):
        return fake

    monkeypatch.setattr(_client_mod.websockets, "connect", fake_connect)


def test_connect_authenticate_and_receive(monkeypatch):
    """Full happy path: connect, auth (dividers stored), decode a binary frame."""

    async def run():
        fake = FakeAsyncWS(incoming=[_AUTH_OK, _market_status_frame()])
        _patch_connect(monkeypatch, fake)

        events = []
        ws = SFeedWebSocket(url="wss://fake/feed")
        ws.on_connect = lambda: events.append("connect")

        await ws.connect()
        # Auth response parsed -> dividers populated, on_connect fired.
        assert ws._authenticated is True
        assert ws.dividers == {1: 100}
        assert events == ["connect"]

        # The auth frame was sent.
        assert any("native_batch" in s for s in fake.sent)

        # Give the receive loop a moment to decode the market-status frame.
        msg = await asyncio.wait_for(ws._message_queue.get(), timeout=1.0)
        assert msg.type == "market_status"

        await ws.close()
        assert fake.closed is True

    asyncio.run(run())


def test_context_manager_and_async_iter(monkeypatch):
    """`async with` + `async for` iterate decoded messages."""

    async def run():
        fake = FakeAsyncWS(incoming=[_AUTH_OK, _market_status_frame()])
        _patch_connect(monkeypatch, fake)

        received = []
        async with SFeedWebSocket(url="wss://fake/feed") as ws:
            async for msg in ws:
                received.append(msg)
                break  # one message is enough
        return received

    received = asyncio.run(run())
    assert len(received) == 1
    assert received[0].type == "market_status"


def test_connect_when_already_connected_raises(monkeypatch):
    async def run():
        fake = FakeAsyncWS(incoming=[_AUTH_OK])
        _patch_connect(monkeypatch, fake)
        ws = SFeedWebSocket(url="wss://fake/feed")
        await ws.connect()
        try:
            await ws.connect()  # second connect -> AlreadyConnectedError
        finally:
            await ws.close()

    with pytest.raises(Exception, match="already connected"):
        asyncio.run(run())


def test_connect_socket_failure_wrapped(monkeypatch):
    async def run():
        async def boom(url, **kwargs):
            raise OSError("dns fail")

        monkeypatch.setattr(_client_mod.websockets, "connect", boom)
        ws = SFeedWebSocket(url="wss://fake/feed")
        await ws.connect()

    with pytest.raises(Exception, match="Failed to connect"):
        asyncio.run(run())


def test_authenticate_timeout(monkeypatch):
    """recv() never yields a str -> auth times out."""

    async def run():
        class NeverAuth(FakeAsyncWS):
            async def recv(self):
                raise TimeoutError

        fake = NeverAuth(incoming=[])
        _patch_connect(monkeypatch, fake)
        ws = SFeedWebSocket(url="wss://fake/feed")
        await ws.connect()

    with pytest.raises(Exception, match="Authentication timeout"):
        asyncio.run(run())


def test_subscribe_over_live_connection(monkeypatch):
    """Subscribe/unsubscribe send frames over a live (fake) connection."""

    async def run():
        fake = FakeAsyncWS(incoming=[_AUTH_OK])
        _patch_connect(monkeypatch, fake)
        ws = SFeedWebSocket(url="wss://fake/feed")
        await ws.connect()

        await ws.subscribe_scrips_lite([WsToken("nse_cm", "1")])
        await ws.subscribe_depth([WsToken("nse_cm", "2")])
        await ws.subscribe_full_depth([WsToken("nse_cm", "3")])
        await ws.subscribe_index([WsToken("nse_cm", "26000")])
        await ws.unsubscribe_scrips_lite([WsToken("nse_cm", "1")])
        await ws.unsubscribe_depth([WsToken("nse_cm", "2")])
        await ws.unsubscribe_full_depth([WsToken("nse_cm", "3")])
        await ws.unsubscribe_index([WsToken("nse_cm", "26000")])

        events = [json.loads(s)["event"] for s in fake.sent if s.startswith("{") and "event" in s]
        await ws.close()
        return events

    events = asyncio.run(run())
    assert "subscribeScripsLite" in events
    assert "subscribeDepth" in events
    assert "subscribeFullDepth" in events
    assert "subscribeIndices" in events
    assert "unsubscribeScripsLite" in events
    assert "unsubscribeDepth" in events
    assert "unsubscribeFullDepth" in events
    assert "unsubscribeIndices" in events


def test_reconnect_resubscribes(monkeypatch):
    """On ConnectionClosed the client reconnects and re-sends subscriptions."""
    import websockets

    async def run():
        # First socket: auth ok, then raises ConnectionClosed on next recv.
        class ClosingWS(FakeAsyncWS):
            async def recv(self):
                if self._incoming:
                    return self._incoming.pop(0)
                raise websockets.exceptions.ConnectionClosed(None, None)

        first = ClosingWS(incoming=[_AUTH_OK])
        second = FakeAsyncWS(incoming=[_AUTH_OK])
        sockets = [first, second]

        async def fake_connect(url, **kwargs):
            return sockets.pop(0)

        monkeypatch.setattr(_client_mod.websockets, "connect", fake_connect)

        ws = SFeedWebSocket(url="wss://fake/feed", reconnect_delay=0, max_reconnect_attempts=2)
        await ws.connect()
        await ws.subscribe_scrips([WsToken("nse_cm", "11536")])

        # Let the receive loop hit ConnectionClosed and reconnect.
        await asyncio.sleep(0.05)

        # Second socket should have received the re-subscribe frame.
        resub = [s for s in second.sent if "subscribeScrips" in s]
        await ws.close()
        return resub

    resub = asyncio.run(run())
    assert len(resub) >= 1


def test_reconnect_gives_up_after_max_attempts(monkeypatch):
    """_handle_disconnect stops after max_reconnect_attempts."""

    async def run():
        async def always_fail(url, **kwargs):
            raise OSError("still down")

        ws = SFeedWebSocket(url="wss://fake/feed", reconnect_delay=0, max_reconnect_attempts=2)
        # Pretend we were connected, then drive disconnect handling directly.
        monkeypatch.setattr(_client_mod.websockets, "connect", always_fail)
        errors = []
        ws.on_error = errors.append
        ws._reconnect_count = 0
        await ws._handle_disconnect()
        return ws._reconnect_count

    # Reaches the cap without hanging.
    count = asyncio.run(run())
    assert count == 2


def test_feed_module_reexports():
    """The feed package re-exports the client symbol."""
    assert feed_module.SFeedWebSocket is SFeedWebSocket
