"""Unit tests for SFeedWebSocket control-plane frame formatting."""

import asyncio
import json

import pytest

# The SFeed client needs `websockets` (a core dependency). Guard defensively so
# the module skips rather than errors if it is somehow missing.
pytest.importorskip("websockets")

from neo_api_client.websocket.feed import SFeedWebSocket, WsToken  # noqa: E402


class FakeWebSocket:
    """Minimal stand-in for a websockets connection that records sent frames."""

    def __init__(self, incoming=None):
        self.sent: list[str] = []
        self._incoming = list(incoming or [])
        self.state = type("S", (), {"name": "OPEN"})()

    async def send(self, data):
        self.sent.append(data)

    async def recv(self):
        return self._incoming.pop(0)

    async def close(self):
        self.state = type("S", (), {"name": "CLOSED"})()


def _client_with_fake_socket():
    ws = SFeedWebSocket()
    ws._ws = FakeWebSocket()
    ws._connected = True
    return ws, ws._ws


def _last_json(fake):
    return json.loads(fake.sent[-1])


def test_subscribe_batches_tokens_into_single_frame():
    async def run():
        ws, fake = _client_with_fake_socket()
        await ws.subscribe_scrips([WsToken("nse_fo", "44498"), WsToken("nse_fo", "44500")])
        return _last_json(fake)

    frame = asyncio.run(run())
    assert frame["event"] == "subscribeScrips"
    assert frame["inputtoken"] == "nse_fo|44498,nse_fo|44500"
    assert frame["json"] == "false"


def test_subscribe_supports_name_token():
    async def run():
        ws, fake = _client_with_fake_socket()
        await ws.subscribe_scrips([WsToken("nse_cm", "Nifty 50")])
        return _last_json(fake)

    frame = asyncio.run(run())
    assert frame["inputtoken"] == "nse_cm|Nifty 50"


def test_unsubscribe_omits_json_field():
    async def run():
        ws, fake = _client_with_fake_socket()
        await ws.unsubscribe_scrips([WsToken("nse_cm", "Nifty 50")])
        return _last_json(fake)

    frame = asyncio.run(run())
    assert frame["event"] == "unsubscribeScrips"
    assert frame["inputtoken"] == "nse_cm|Nifty 50"
    assert "json" not in frame


def test_auth_frame_fields():
    ws, _ = _client_with_fake_socket()
    frame = ws._build_auth_frame()
    assert frame["user"] == "neome"
    assert frame["auth"] == "1"
    assert frame["format"] == "native_batch"
    assert frame["source"] == "SFeed"
    assert frame["platform"] == "Web"
    assert frame["version"] == "1.2.3"
    assert frame["sdk_version"] == 2
    assert frame["sessionValidation"] is False
    assert isinstance(frame["conn_req_time"], int)


def test_subscribe_index_event_name():
    async def run():
        ws, fake = _client_with_fake_socket()
        await ws.subscribe_index([WsToken("nse_cm", "26000")])
        return _last_json(fake)

    frame = asyncio.run(run())
    assert frame["event"] == "subscribeIndices"


def test_empty_token_list_sends_nothing():
    async def run():
        ws, fake = _client_with_fake_socket()
        await ws.subscribe_scrips([])
        return fake.sent

    assert asyncio.run(run()) == []


def test_subscription_state_tracked_for_reconnect():
    async def run():
        ws, _ = _client_with_fake_socket()
        await ws.subscribe_scrips([WsToken("nse_cm", "11536")])
        return ws._subscriptions

    subs = asyncio.run(run())
    assert (WsToken("nse_cm", "11536"), "scrips") in subs


# Real SFeed production auth response (message_code 1119, dividers keyed by value).
_AUTH_1119 = {
    "message_code": 1119,
    "id": "SFD_CPROD_701",
    "version": 1,
    "exchanges": {
        "nse_cm": {"value": 1, "divider": 100},
        "nse_fo": {"value": 2, "divider": 100},
        "cde_fo": {"value": 3, "divider": 10000000},
        "bse_cd": {"value": 7, "divider": 10000000},
    },
}


def test_authenticate_accepts_1119_and_stores_dividers():
    async def run():
        ws = SFeedWebSocket()
        ws._ws = FakeWebSocket(incoming=[json.dumps(_AUTH_1119)])
        ws._connected = True
        await ws._authenticate()
        return ws

    ws = asyncio.run(run())
    assert ws._authenticated is True
    # Dividers keyed by the response's own exchange "value".
    assert ws._dividers[1] == 100  # nse_cm
    assert ws._dividers[3] == 10000000  # cde_fo
    assert ws._dividers[7] == 10000000  # bse_cd


def test_authenticate_rejects_unknown_message_code():
    async def run():
        ws = SFeedWebSocket()
        ws._ws = FakeWebSocket(incoming=[json.dumps({"message_code": 9999})])
        ws._connected = True
        await ws._authenticate()

    with pytest.raises(Exception, match="Unexpected auth response"):
        asyncio.run(run())


def test_authenticate_rejects_native_fallback():
    async def run():
        ws = SFeedWebSocket()
        resp = {"message_code": 1119, "format": "native_fallback", "exchanges": {}}
        ws._ws = FakeWebSocket(incoming=[json.dumps(resp)])
        ws._connected = True
        await ws._authenticate()

    with pytest.raises(Exception, match="native_fallback"):
        asyncio.run(run())


# ---- is_connected state logic ----------------------------------------------


def test_is_connected_false_when_no_socket():
    ws = SFeedWebSocket()
    assert ws.is_connected is False


def test_is_connected_uses_state_open():
    ws, fake = _client_with_fake_socket()
    assert ws.is_connected is True


def test_is_connected_false_when_state_closed():
    ws, fake = _client_with_fake_socket()
    fake.state = type("S", (), {"name": "CLOSED"})()
    assert ws.is_connected is False


def test_is_connected_respects_closed_attr():
    ws = SFeedWebSocket()
    ws._connected = True
    ws._ws = type("W", (), {"closed": True})()
    assert ws.is_connected is False


# ---- dividers property ------------------------------------------------------


def test_dividers_property_returns_copy():
    ws = SFeedWebSocket()
    ws._dividers = {1: 100}
    d = ws.dividers
    assert d == {1: 100}
    d[2] = 999  # mutating the copy must not affect internal state
    assert 2 not in ws._dividers


# ---- __anext__ --------------------------------------------------------------


def test_anext_raises_when_not_connected():
    ws = SFeedWebSocket()

    async def run():
        await ws.__anext__()

    with pytest.raises(Exception, match="not connected"):
        asyncio.run(run())


def test_anext_returns_queued_message():
    async def run():
        ws, _ = _client_with_fake_socket()
        await ws._message_queue.put("hello")
        return await ws.__anext__()

    assert asyncio.run(run()) == "hello"


# ---- binary frame handling --------------------------------------------------


def _market_status_frame():
    """Build a 9-byte market-OPEN packet (header only)."""
    import struct

    from neo_api_client.websocket.feed.protocol import HEADER_SIZE, MSG_MARKET_OPEN

    header = struct.Struct("<HHbBBBB")
    return header.pack(HEADER_SIZE, MSG_MARKET_OPEN, 1, 0, 0, 0, 0)


def test_handle_binary_frame_enqueues_and_calls_on_message():
    ws, _ = _client_with_fake_socket()
    received = []
    ws.on_message = received.append

    ws._handle_binary_frame(_market_status_frame())

    assert ws._message_queue.qsize() == 1
    assert len(received) == 1
    assert received[0].type == "market_status"


def test_handle_binary_frame_ignores_unknown_packet():
    ws, _ = _client_with_fake_socket()
    import struct

    # Unknown message_code, level 0 -> decode returns None -> nothing enqueued.
    header = struct.Struct("<HHbBBBB")
    frame = header.pack(9, 9999, 1, 0, 0, 0, 0)

    ws._handle_binary_frame(frame)
    assert ws._message_queue.qsize() == 0


# ---- close ------------------------------------------------------------------


def test_close_resets_state_and_calls_on_disconnect():
    async def run():
        ws, _ = _client_with_fake_socket()
        events = []
        ws.on_disconnect = lambda: events.append("disconnected")
        await ws.close()
        return ws, events

    ws, events = asyncio.run(run())
    assert ws._connected is False
    assert ws._authenticated is False
    assert ws._ws is None
    assert events == ["disconnected"]


# ---- snapshot ---------------------------------------------------------------


def test_snapshot_sends_frame():
    async def run():
        ws, fake = _client_with_fake_socket()
        await ws.snapshot([WsToken("nse_cm", "11536")], intent="scrips")
        return _last_json(fake)

    frame = asyncio.run(run())
    assert frame["event"] == "snapshotScrips"
    assert frame["inputtoken"] == "nse_cm|11536"


def test_snapshot_invalid_intent_raises():
    async def run():
        ws, _ = _client_with_fake_socket()
        await ws.snapshot([WsToken("nse_cm", "11536")], intent="bogus")

    with pytest.raises(Exception, match="Snapshot not supported"):
        asyncio.run(run())


# ---- not-connected guards ---------------------------------------------------


def test_subscribe_when_not_connected_raises():
    ws = SFeedWebSocket()  # never connected

    async def run():
        await ws.subscribe_scrips([WsToken("nse_cm", "11536")])

    with pytest.raises(Exception, match="not connected"):
        asyncio.run(run())
