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
from neo_api_client.websocket.feed.exceptions import NotConnectedError  # noqa: E402
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
                # Use asyncio.TimeoutError explicitly: on Python 3.10 it is a
                # distinct class from the builtin TimeoutError (they were merged
                # in 3.11), and the client catches asyncio.TimeoutError.
                raise asyncio.TimeoutError

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


# ---- TLS verification -------------------------------------------------------


def test_connect_verifies_tls_by_default(monkeypatch):
    """Default connect() uses a cert-verifying SSL context for wss://."""

    async def run():
        captured = {}
        fake = FakeAsyncWS(incoming=[_AUTH_OK])

        async def fake_connect(url, **kwargs):
            captured["ssl"] = kwargs.get("ssl")
            return fake

        monkeypatch.setattr(_client_mod.websockets, "connect", fake_connect)
        ws = SFeedWebSocket(url="wss://fake/feed")
        await ws.connect()
        await ws.close()
        return captured["ssl"]

    import ssl as _ssl

    ctx = asyncio.run(run())
    assert ctx is not None
    assert ctx.verify_mode == _ssl.CERT_REQUIRED
    assert ctx.check_hostname is True


def test_connect_verify_ssl_false_disables_and_warns(monkeypatch):
    """verify_ssl=False disables verification and emits a warning."""

    async def run():
        captured = {}
        fake = FakeAsyncWS(incoming=[_AUTH_OK])

        async def fake_connect(url, **kwargs):
            captured["ssl"] = kwargs.get("ssl")
            return fake

        monkeypatch.setattr(_client_mod.websockets, "connect", fake_connect)
        ws = SFeedWebSocket(url="wss://fake/feed", verify_ssl=False)
        await ws.connect()
        await ws.close()
        return captured["ssl"]

    import ssl as _ssl

    with pytest.warns(UserWarning, match="man-in-the-middle"):
        ctx = asyncio.run(run())

    assert ctx.verify_mode == _ssl.CERT_NONE
    assert ctx.check_hostname is False


# ---- __anext__ / is_connected -----------------------------------------------


def test_anext_raises_when_not_connected():
    ws = SFeedWebSocket(url="wss://fake/feed")

    async def run():
        await ws.__anext__()

    with pytest.raises(NotConnectedError):
        asyncio.run(run())


def test_anext_stops_iteration_when_disconnected_after_timeout():
    async def run():
        ws = SFeedWebSocket(url="wss://fake/feed")
        ws._connected = True  # connected but queue stays empty, no socket

        async def flip():
            await asyncio.sleep(0.05)
            ws._connected = False

        asyncio.create_task(flip())
        with pytest.raises(StopAsyncIteration):
            await ws.__anext__()

    asyncio.run(run())


def test_anext_recurses_after_timeout_then_returns():
    async def run():
        ws = SFeedWebSocket(url="wss://fake/feed")
        ws._connected = True

        async def deliver():
            await asyncio.sleep(1.2)  # force one wait_for timeout first
            ws._message_queue.put_nowait("late")

        asyncio.create_task(deliver())
        return await ws.__anext__()

    assert asyncio.run(run()) == "late"


def test_is_connected_true_when_socket_has_no_state_or_closed():
    ws = SFeedWebSocket(url="wss://fake/feed")
    ws._connected = True
    ws._ws = object()  # no closed / state attribute -> assumed open
    assert ws.is_connected is True


# ---- receive loop callbacks -------------------------------------------------


def test_receive_loop_invokes_on_raw_and_ignores_text(monkeypatch):
    """on_raw fires for every frame; a post-auth text frame is ignored (no crash)."""

    async def run():
        # After auth, deliver a control text frame then a binary market-status frame.
        fake = FakeAsyncWS(incoming=[_AUTH_OK, '{"event":"ack"}', _market_status_frame()])
        _patch_connect(monkeypatch, fake)

        raw_frames = []
        ws = SFeedWebSocket(url="wss://fake/feed")
        ws.on_raw = raw_frames.append

        await ws.connect()
        # Let the receive loop process the ack (ignored) + binary (decoded).
        msg = await asyncio.wait_for(ws._message_queue.get(), timeout=1.0)
        await ws.close()
        return raw_frames, msg

    raw_frames, msg = asyncio.run(run())
    assert any(isinstance(f, str) for f in raw_frames)  # text ack seen by on_raw
    assert msg.type == "market_status"


# ---- _authenticate generic failure ------------------------------------------


def test_authenticate_generic_failure_wrapped(monkeypatch):
    """A non-timeout error during auth is wrapped as AuthenticationError."""

    async def run():
        class BadJSON(FakeAsyncWS):
            async def recv(self):
                return "not-json{"  # json.loads raises -> generic except branch

        fake = BadJSON(incoming=[])
        _patch_connect(monkeypatch, fake)
        ws = SFeedWebSocket(url="wss://fake/feed")
        await ws.connect()

    with pytest.raises(Exception, match="Authentication failed"):
        asyncio.run(run())


# ---- _handle_disconnect callback + no-op ------------------------------------


def test_handle_disconnect_fires_on_disconnect_and_stops_at_cap(monkeypatch):
    async def run():
        async def always_fail(url, **kwargs):
            raise OSError("down")

        monkeypatch.setattr(_client_mod.websockets, "connect", always_fail)
        ws = SFeedWebSocket(url="wss://fake/feed", reconnect_delay=0, max_reconnect_attempts=1)
        events = []
        ws.on_disconnect = lambda: events.append("disc")
        ws._reconnect_count = 0
        await ws._handle_disconnect()
        return ws._reconnect_count, events

    count, events = asyncio.run(run())
    assert count == 1
    assert events  # on_disconnect fired


# ---- _subscribe error wrapping ----------------------------------------------


def test_subscribe_send_failure_wrapped(monkeypatch):
    """A send failure during subscribe is wrapped as SubscriptionError."""
    from neo_api_client.websocket.feed.exceptions import SubscriptionError

    async def run():
        fake = FakeAsyncWS(incoming=[_AUTH_OK])
        _patch_connect(monkeypatch, fake)
        ws = SFeedWebSocket(url="wss://fake/feed")
        await ws.connect()

        async def boom(*a, **k):
            raise RuntimeError("send broke")

        ws._ws.send = boom
        try:
            await ws.subscribe_scrips([WsToken("nse_cm", "1")])
        finally:
            ws._connected = False

    with pytest.raises(SubscriptionError, match="Failed to subscribe"):
        asyncio.run(run())


def test_subscribe_over_limit_raises(monkeypatch):
    """Exceeding max_subscriptions raises SubscriptionError and sends nothing."""
    from neo_api_client.websocket.feed.exceptions import SubscriptionError

    async def run():
        fake = FakeAsyncWS(incoming=[_AUTH_OK])
        _patch_connect(monkeypatch, fake)
        ws = SFeedWebSocket(url="wss://fake/feed", max_subscriptions=1)
        await ws.connect()
        try:
            await ws.subscribe_scrips([WsToken("nse_cm", "1"), WsToken("nse_cm", "2")])
        finally:
            ws._connected = False

    with pytest.raises(SubscriptionError, match="limit exceeded"):
        asyncio.run(run())


# ---- authenticate: skip pre-auth binary frames + divider fallbacks ----------


def test_authenticate_skips_binary_and_uses_divider_fallbacks(monkeypatch):
    """Auth loop skips a leading binary frame before the JSON auth response,
    and the dividers loop tolerates a non-dict entry and a name-only entry
    resolved via EXCHANGE_NAME_TO_ID (client.py 278-283, 294-298)."""

    async def run():
        auth = json.dumps(
            {
                "message_code": 1119,
                "format": "native_batch",
                "exchanges": {
                    "nse_cm": {"value": 1, "divider": 100},
                    "nse_fo": {"divider": 50},  # no "value" -> fallback to name map (id 2)
                    "bogus": "not-a-dict",  # non-dict -> skipped
                },
            }
        )
        # A binary frame arrives BEFORE the JSON auth response and must be skipped.
        fake = FakeAsyncWS(incoming=[b"\x00\x01binary-preamble", auth])
        _patch_connect(monkeypatch, fake)

        ws = SFeedWebSocket(url="wss://fake/feed")
        await ws.connect()
        dividers = ws.dividers
        await ws.close()
        return dividers

    dividers = asyncio.run(run())
    assert dividers[1] == 100  # nse_cm by explicit value
    assert dividers[2] == 50  # nse_fo resolved via EXCHANGE_NAME_TO_ID fallback


# ---- _subscribe re-raises an inner SubscriptionError ------------------------


def test_subscribe_reraises_subscription_error(monkeypatch):
    """If sending a subscribe frame raises SubscriptionError, it propagates
    unchanged rather than being re-wrapped (client.py line 409)."""
    from neo_api_client.websocket.feed.exceptions import SubscriptionError

    async def run():
        fake = FakeAsyncWS(incoming=[_AUTH_OK])
        _patch_connect(monkeypatch, fake)
        ws = SFeedWebSocket(url="wss://fake/feed")
        await ws.connect()

        async def raise_sub_error(*a, **k):
            raise SubscriptionError("inner limit hit")

        monkeypatch.setattr(ws, "_send_subscribe", raise_sub_error)
        try:
            await ws.subscribe_scrips([WsToken("nse_cm", "1")])
        finally:
            ws._connected = False

    with pytest.raises(SubscriptionError, match="inner limit hit"):
        asyncio.run(run())


# ---- remaining auth / connect branch edges ----------------------------------


def test_authenticate_exhausts_without_json_response(monkeypatch):
    """If 10 frames arrive and none is a str, the auth loop gives up (278->283)."""

    async def run():
        # Only binary frames -> `data` stays None -> "Unexpected auth response".
        fake = FakeAsyncWS(incoming=[b"\x00" * 4] * 12)
        _patch_connect(monkeypatch, fake)
        ws = SFeedWebSocket(url="wss://fake/feed")
        await ws.connect()

    with pytest.raises(Exception, match="Unexpected auth response"):
        asyncio.run(run())


def test_authenticate_skips_unresolvable_exchange(monkeypatch):
    """A dict exchange entry with no 'value' and an unknown name yields no id,
    so it is skipped (298->294)."""

    async def run():
        auth = json.dumps(
            {
                "message_code": 1119,
                "format": "native_batch",
                "exchanges": {
                    "nse_cm": {"value": 1, "divider": 100},
                    "totally_unknown_exchange": {"divider": 25},  # no value, unknown name
                },
            }
        )
        fake = FakeAsyncWS(incoming=[auth])
        _patch_connect(monkeypatch, fake)
        ws = SFeedWebSocket(url="wss://fake/feed")
        await ws.connect()
        dividers = ws.dividers
        await ws.close()
        return dividers

    dividers = asyncio.run(run())
    assert dividers == {1: 100}  # unknown exchange skipped, no bogus entry added


def test_connect_plain_ws_scheme_skips_ssl(monkeypatch):
    """A ws:// (non-TLS) URL connects with ssl=None (217->231 false branch)."""

    async def run():
        captured = {}

        async def fake_connect(url, **kwargs):
            captured["ssl"] = kwargs.get("ssl")
            return FakeAsyncWS(incoming=[_AUTH_OK])

        monkeypatch.setattr(_client_mod.websockets, "connect", fake_connect)
        ws = SFeedWebSocket(url="ws://localhost:9000/feed")
        await ws.connect()
        await ws.close()
        return captured["ssl"]

    assert asyncio.run(run()) is None  # no TLS context for ws://
