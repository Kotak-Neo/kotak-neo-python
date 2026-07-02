"""Unit tests for SFeedWebSocket control-plane frame formatting."""

import asyncio
import json

import pytest

# The SFeed client requires the optional `websockets` dependency (the `feed`
# extra). Skip this module cleanly when it isn't installed.
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
