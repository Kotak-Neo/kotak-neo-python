"""Unit tests for the Order & Position streaming WebSocket client."""

import asyncio
import json

import pytest

pytest.importorskip("websockets")

from neo_api_client import NeoAPI  # noqa: E402
from neo_api_client.websocket.orderfeed import (  # noqa: E402
    OrderFeedWebSocket,
    OrderStatus,
    OrderUpdate,
    PositionUpdate,
)
from neo_api_client.websocket.orderfeed import client as _client_mod  # noqa: E402
from neo_api_client.websocket.orderfeed.client import _to_realtime_url  # noqa: E402


class FakeAsyncWS:
    """Scripted async WebSocket; recv() yields queued frames then idles."""

    def __init__(self, incoming=None):
        self.sent = []
        self._incoming = list(incoming or [])
        self.state = type("S", (), {"name": "OPEN"})()
        self.closed = False

    async def send(self, data):
        self.sent.append(data)

    async def recv(self):
        if self._incoming:
            return self._incoming.pop(0)
        await asyncio.sleep(3600)

    async def close(self):
        self.closed = True
        self.state = type("S", (), {"name": "CLOSED"})()


def _patch_connect(monkeypatch, fake):
    async def fake_connect(url, **kwargs):
        return fake

    monkeypatch.setattr(_client_mod.websockets, "connect", fake_connect)


# ---- URL derivation ---------------------------------------------------------


def test_to_realtime_url_https():
    assert _to_realtime_url("https://e21.kotaksecurities.com") == (
        "wss://e21.kotaksecurities.com/realtime"
    )


def test_to_realtime_url_bare_host():
    assert _to_realtime_url("e22.kotaksecurities.com") == ("wss://e22.kotaksecurities.com/realtime")


def test_explicit_url_takes_priority_over_base_url():
    """A pre-resolved url (e.g. from the dynamic config service) overrides base_url-derivation."""
    ws = OrderFeedWebSocket(
        base_url="https://e21.kotaksecurities.com",
        url="https://e99.kotaksecurities.com/realtime",
        auth="TOK",
        sid="SID",
    )
    assert ws.url == "wss://e99.kotaksecurities.com/realtime"


def test_explicit_url_normalizes_http_to_ws():
    ws = OrderFeedWebSocket(base_url=None, url="http://fake/realtime", auth="TOK", sid="SID")
    assert ws.url == "ws://fake/realtime"


def test_no_url_and_no_base_url_leaves_url_none():
    ws = OrderFeedWebSocket(base_url=None, auth="TOK", sid="SID")
    assert ws.url is None


# ---- auth payload -----------------------------------------------------------


def test_auth_payload_is_raw_non_json():
    ws = OrderFeedWebSocket(base_url="https://e21.kotaksecurities.com", auth="TOK", sid="SID")
    payload = ws._build_auth_payload()
    assert payload == "{type:cn,Authorization:TOK,Sid:SID,src:WEB}"
    # Must NOT be valid JSON (it's a raw string per the spec).
    with pytest.raises(ValueError):
        json.loads(payload)


def test_auth_payload_custom_source():
    ws = OrderFeedWebSocket(base_url="https://e21.x.com", auth="T", sid="S", source="MOBILE")
    assert ws._build_auth_payload() == "{type:cn,Authorization:T,Sid:S,src:MOBILE}"


# ---- message parsing --------------------------------------------------------


def _ws():
    return OrderFeedWebSocket(base_url="https://e21.x.com", auth="T", sid="S")


def test_parse_connection_ack_is_dropped():
    ack = '{"ak":"ok","type":"cn","task":"cn","msg":"connected"}'
    assert _ws()._parse_message(ack) is None


def test_parse_order_message_maps_all_fields():
    frame = json.dumps({
        "type": "order",
        "data": {
            "nOrdNo": "260216000308219",
            "ordSt": "complete",
            "avgPrc": "35.88",
            "qty": 1,
            "fldQty": 1,
            "unFldSz": 0,
            "sym": "ITBEES",
            "trnsTp": "B",
            "prcTp": "MKT",
            "prod": "NRML",
            "exSeg": "nse_cm",
            "trdSym": "ITBEES-EQ",
            "tok": "14428",
            "ordDtTm": "16-Feb-2026 12:29:31",
            "updRecvTm": 1739688571000000000,
            "boeSec": 1739688571,
            "exCfmTm": "16-Feb-2026 12:29:32",
            "exOrdId": "1100000049435826",
        },
    })
    msg = _ws()._parse_message(frame)
    assert isinstance(msg, OrderUpdate)
    d = msg.data
    assert d.order_id == "260216000308219"
    assert d.order_status == "complete"
    assert d.average_price == "35.88"
    assert d.quantity == 1
    assert d.filled_quantity == 1
    assert d.unfilled_size == 0
    assert d.symbol == "ITBEES"
    assert d.transaction_type == "B"
    assert d.price_type == "MKT"
    assert d.product == "NRML"
    assert d.exchange_segment == "nse_cm"
    assert d.trading_symbol == "ITBEES-EQ"
    assert d.token == "14428"
    assert d.order_date_time == "16-Feb-2026 12:29:31"
    assert d.update_receive_time == 1739688571000000000
    assert d.exchange_broadcast_time == 1739688571
    assert d.exchange_confirmation_time == "16-Feb-2026 12:29:32"
    assert d.exchange_order_id == "1100000049435826"


def test_parse_position_message():
    frame = json.dumps({
        "type": "position",
        "data": {
            "actId": "XP6M4",
            "sym": "ITBEES",
            "exSeg": "nse_cm",
            "prod": "NRML",
            "flBuyQty": "1",
            "flSellQty": "0",
            "buyAmt": "35.88",
            "sellAmt": "0.00",
            "posFlg": "true",
            "sqrFlg": "true",
            "lotSz": "1",
            "multiplier": "1",
            "hsUpTm": "2026/02/16 12:29:31",
        },
    })
    msg = _ws()._parse_message(frame)
    assert isinstance(msg, PositionUpdate)
    d = msg.data
    assert d.account_id == "XP6M4"
    assert d.symbol == "ITBEES"
    assert d.exchange_segment == "nse_cm"
    assert d.product == "NRML"
    assert d.filled_buy_quantity == "1"
    assert d.filled_sell_quantity == "0"
    assert d.buy_amount == "35.88"
    assert d.sell_amount == "0.00"
    assert d.position_flag == "true"
    assert d.square_off_flag == "true"
    assert d.lot_size == "1"
    assert d.multiplier == "1"
    assert d.update_time == "2026/02/16 12:29:31"


def test_order_status_constants_match_lifecycle():
    """OrderStatus exposes the observed lifecycle values for comparison."""
    assert OrderStatus.PUT_ORDER_REQ_RECEIVED == "put order req received"
    assert OrderStatus.VALIDATION_PENDING == "validation pending"
    assert OrderStatus.OPEN_PENDING == "open pending"
    assert OrderStatus.OPEN == "open"
    assert OrderStatus.COMPLETE == "complete"
    assert OrderStatus.REJECTED == "rejected"
    assert OrderStatus.CANCELLED == "cancelled"
    assert OrderStatus.MODIFIED == "modified"


def test_order_status_usable_for_comparison():
    frame = '{"type":"order","data":{"nOrdNo":"1","ordSt":"complete"}}'
    msg = _ws()._parse_message(frame)
    assert msg.data.order_status == OrderStatus.COMPLETE


def test_unknown_order_status_still_parsed():
    """An unlisted status is surfaced as-is (order_status is a plain string)."""
    frame = '{"type":"order","data":{"nOrdNo":"1","ordSt":"some_future_state"}}'
    msg = _ws()._parse_message(frame)
    assert msg.data.order_status == "some_future_state"


def test_parse_unknown_type_returns_raw_dict():
    assert _ws()._parse_message('{"type":"heartbeat","x":1}') == {"type": "heartbeat", "x": 1}


def test_parse_non_json_returns_raw_string():
    assert _ws()._parse_message("PING") == "PING"


# ---- connect + stream -------------------------------------------------------


def test_connect_sends_payload_and_streams(monkeypatch):
    async def run():
        order_frame = '{"type":"order","data":{"nOrdNo":"1","ordSt":"open","sym":"ITBEES"}}'
        fake = FakeAsyncWS(incoming=[order_frame, "plain-text-frame"])
        _patch_connect(monkeypatch, fake)

        events = []
        ws = OrderFeedWebSocket(base_url="https://e21.kotaksecurities.com", auth="TOK", sid="SID")
        ws.on_connect = lambda: events.append("connect")

        await ws.connect()
        # Raw non-JSON connection payload was sent.
        assert fake.sent == ["{type:cn,Authorization:TOK,Sid:SID,src:WEB}"]
        assert events == ["connect"]

        # JSON order frame decodes to a typed OrderUpdate.
        msg1 = await asyncio.wait_for(ws._message_queue.get(), timeout=1.0)
        # Non-JSON frame passes through as a string.
        msg2 = await asyncio.wait_for(ws._message_queue.get(), timeout=1.0)

        await ws.close()
        return msg1, msg2, fake.closed

    msg1, msg2, closed = asyncio.run(run())
    assert isinstance(msg1, OrderUpdate)
    assert msg1.data.order_id == "1"
    assert msg1.data.order_status == "open"
    assert msg1.data.symbol == "ITBEES"
    assert msg2 == "plain-text-frame"
    assert closed is True


def test_order_update_packet_logs_order_id_and_status(monkeypatch):
    """Every received order packet is logged with order_id + order_status --
    QA's audit-trail ask -- not just connection lifecycle events."""

    async def run():
        order_frame = '{"type":"order","data":{"nOrdNo":"1","ordSt":"open","sym":"ITBEES"}}'
        fake = FakeAsyncWS(incoming=[order_frame])
        _patch_connect(monkeypatch, fake)

        logged = {}
        orig_info = _client_mod.logger.info

        def capture_info(event, **kwargs):
            if event == "orderfeed_order_update":
                logged.update(kwargs, event=event)
            return orig_info(event, **kwargs)

        monkeypatch.setattr(_client_mod.logger, "info", capture_info)

        ws = OrderFeedWebSocket(base_url="https://e21.kotaksecurities.com", auth="TOK", sid="SID")
        await ws.connect()
        await asyncio.wait_for(ws._message_queue.get(), timeout=1.0)
        await ws.close()
        return logged

    logged = asyncio.run(run())
    assert logged["order_id"] == "1"
    assert logged["order_status"] == "open"
    assert logged["trading_symbol"] is None  # sym maps to `symbol`, not `trading_symbol`


def test_connect_logs_connected_and_authenticated_at_info(monkeypatch):
    """A healthy connect must be visible at INFO -- a customer running at the
    recommended INFO level (not the SDK-internal DEBUG level) should see
    confirmation the order feed is up, not just errors."""

    async def run():
        fake = FakeAsyncWS(incoming=[])
        _patch_connect(monkeypatch, fake)

        logged_events = []
        orig_info = _client_mod.logger.info

        def capture_info(event, **kwargs):
            logged_events.append(event)
            return orig_info(event, **kwargs)

        monkeypatch.setattr(_client_mod.logger, "info", capture_info)

        ws = OrderFeedWebSocket(base_url="https://e21.kotaksecurities.com", auth="TOK", sid="SID")
        await ws.connect()
        await ws.close()
        return logged_events

    logged_events = asyncio.run(run())
    assert "orderfeed_connected" in logged_events
    assert "orderfeed_authenticated" in logged_events


def test_context_manager_and_async_iter(monkeypatch):
    async def run():
        fake = FakeAsyncWS(incoming=['{"type":"position","data":{"sym":"ITBEES","netQty":10}}'])
        _patch_connect(monkeypatch, fake)
        received = []
        async with OrderFeedWebSocket(base_url="https://e21.x.com", auth="T", sid="S") as ws:
            async for message in ws:
                received.append(message)
                break
        return received

    received = asyncio.run(run())
    assert len(received) == 1
    assert isinstance(received[0], PositionUpdate)
    assert received[0].data.symbol == "ITBEES"


def test_connect_already_connected_raises(monkeypatch):
    async def run():
        fake = FakeAsyncWS()
        _patch_connect(monkeypatch, fake)
        ws = OrderFeedWebSocket(base_url="https://e21.x.com", auth="T", sid="S")
        await ws.connect()
        try:
            await ws.connect()
        finally:
            await ws.close()

    with pytest.raises(Exception, match="already connected"):
        asyncio.run(run())


def test_connect_socket_failure_wrapped(monkeypatch):
    async def run():
        async def boom(url, **kwargs):
            raise OSError("dns fail")

        monkeypatch.setattr(_client_mod.websockets, "connect", boom)
        # max_connect_retries=0: fail immediately, no retry delay to wait out.
        ws = OrderFeedWebSocket(
            base_url="https://e21.x.com", auth="T", sid="S", max_connect_retries=0
        )
        await ws.connect()

    with pytest.raises(Exception, match="Failed to connect"):
        asyncio.run(run())


def test_connect_retries_then_succeeds(monkeypatch):
    """The first couple of failures are retried; a later success within
    max_connect_retries is used, and no exception is raised."""

    async def run():
        attempts = []

        async def flaky(url, **kwargs):
            attempts.append(1)
            if len(attempts) < 3:
                raise OSError("transient")
            return FakeAsyncWS()

        monkeypatch.setattr(_client_mod.websockets, "connect", flaky)
        ws = OrderFeedWebSocket(
            base_url="https://e21.x.com",
            auth="T",
            sid="S",
            max_connect_retries=3,
            reconnect_delay=0,
        )
        await ws.connect()
        assert ws.is_connected
        assert len(attempts) == 3
        await ws.close()

    asyncio.run(run())


def test_connect_exhausts_all_retries_then_raises(monkeypatch):
    """After max_connect_retries+1 total failed attempts, the last error is
    wrapped and raised."""

    async def run():
        attempts = []

        async def always_boom(url, **kwargs):
            attempts.append(1)
            raise OSError(f"dns fail #{len(attempts)}")

        monkeypatch.setattr(_client_mod.websockets, "connect", always_boom)
        ws = OrderFeedWebSocket(
            base_url="https://e21.x.com",
            auth="T",
            sid="S",
            max_connect_retries=3,
            reconnect_delay=0,
        )
        await ws.connect()

    with pytest.raises(Exception, match="Failed to connect after 4 attempt"):
        asyncio.run(run())


def test_connect_without_base_url_raises():
    async def run():
        ws = OrderFeedWebSocket(base_url="", auth="T", sid="S")
        await ws.connect()

    with pytest.raises(Exception, match="No base URL"):
        asyncio.run(run())


def test_reconnect_on_connection_closed(monkeypatch):
    import websockets

    async def run():
        class ClosingWS(FakeAsyncWS):
            async def recv(self):
                if self._incoming:
                    return self._incoming.pop(0)
                raise websockets.exceptions.ConnectionClosed(None, None)

        first = ClosingWS(incoming=['{"type":"order"}'])
        second = FakeAsyncWS()
        sockets = [first, second]

        async def fake_connect(url, **kwargs):
            return sockets.pop(0)

        monkeypatch.setattr(_client_mod.websockets, "connect", fake_connect)

        ws = OrderFeedWebSocket(
            base_url="https://e21.x.com",
            auth="T",
            sid="S",
            reconnect_delay=0,
            max_reconnect_attempts=2,
        )
        await ws.connect()
        await asyncio.sleep(0.05)
        # Second socket also received the raw connection payload on reconnect.
        resent = [s for s in second.sent if s.startswith("{type:cn")]
        await ws.close()
        return resent

    assert len(asyncio.run(run())) >= 1


# ---- NeoAPI.create_order_feed ----------------------------------------------


def _authed_client():
    c = NeoAPI(environment="prod", consumer_key="ck")
    c.configuration.edit_token = "trade_token"
    c.configuration.edit_sid = "sid_123"
    c.configuration.base_url = "https://e21.kotaksecurities.com"
    return c


def test_create_order_feed_returns_configured_client():
    feed = _authed_client().create_order_feed()
    assert isinstance(feed, OrderFeedWebSocket)
    assert feed.url == "wss://e21.kotaksecurities.com/realtime"
    assert feed.auth == "trade_token"
    assert feed.sid == "sid_123"


def test_create_order_feed_requires_auth():
    c = NeoAPI(environment="prod", consumer_key="ck")
    with pytest.raises(ValueError, match="Authentication required"):
        c.create_order_feed()


def test_create_order_feed_requires_base_url():
    c = NeoAPI(environment="prod", consumer_key="ck")
    c.configuration.edit_token = "t"
    c.configuration.edit_sid = "s"
    # base_url stays None, and data_center is unset -> no hardcoded fallback either.
    with pytest.raises(ValueError, match="base URL is unavailable"):
        c.create_order_feed()


def test_create_order_feed_prefers_dynamic_config_url_over_base_url():
    """When resolve_dynamic_urls() populated order_feed_url, it wins over base_url."""
    c = _authed_client()
    c.configuration.order_feed_url = "https://e21.kotaksecurities.com/realtime"

    feed = c.create_order_feed()

    assert feed.url == "wss://e21.kotaksecurities.com/realtime"


def test_create_order_feed_explicit_url_kwarg_wins_over_dynamic_config():
    c = _authed_client()
    c.configuration.order_feed_url = "https://e21.kotaksecurities.com/realtime"

    feed = c.create_order_feed(url="https://override.example.com/realtime")

    assert feed.url == "wss://override.example.com/realtime"


def test_create_order_feed_uses_rt_url_when_dynamic_config_missing():
    """totp_validate()'s rtUrl is used (ahead of base_url-derivation) when the
    dynamic config service didn't resolve order_feed_url."""
    c = _authed_client()  # base_url is set, order_feed_url is not
    c.configuration.rt_url = "https://login-rt.kotaksecurities.com/realtime"

    feed = c.create_order_feed()

    assert feed.url == "wss://login-rt.kotaksecurities.com/realtime"


def test_create_order_feed_dynamic_config_wins_over_rt_url():
    """order_feed_url (dynamic config) takes priority over rt_url (totp_validate)."""
    c = _authed_client()
    c.configuration.order_feed_url = "https://config.example.com/realtime"
    c.configuration.rt_url = "https://login-rt.kotaksecurities.com/realtime"

    feed = c.create_order_feed()

    assert feed.url == "wss://config.example.com/realtime"


def test_create_order_feed_base_url_wins_over_rt_url_when_rt_url_absent():
    """Confirms rt_url is an EXTRA layer, not a replacement: with neither
    order_feed_url nor rt_url set, base_url-derivation still applies
    (existing behavior, unchanged)."""
    c = _authed_client()  # base_url = "https://e21.kotaksecurities.com"

    feed = c.create_order_feed()

    assert feed.url == "wss://e21.kotaksecurities.com/realtime"


def test_create_order_feed_falls_back_to_hardcoded_constant_when_base_url_missing():
    """No dynamic config value and no base_url, but data_center matches a known
    ORDER_FEED_URL_* constant -> use it instead of raising."""
    c = NeoAPI(environment="prod", consumer_key="ck")
    c.configuration.edit_token = "t"
    c.configuration.edit_sid = "s"
    c.configuration.data_center = "E21"
    # base_url and order_feed_url both stay None.

    feed = c.create_order_feed()

    assert feed.url == "wss://e21.kotaksecurities.com/realtime"


def test_create_order_feed_unrecognized_data_center_still_raises():
    c = NeoAPI(environment="prod", consumer_key="ck")
    c.configuration.edit_token = "t"
    c.configuration.edit_sid = "s"
    c.configuration.data_center = "E25"  # no ORDER_FEED_URL_E25 constant exists
    # base_url and order_feed_url both stay None.

    with pytest.raises(ValueError, match="base URL is unavailable"):
        c.create_order_feed()


# ---- __anext__ / is_connected -----------------------------------------------


def test_anext_raises_when_not_connected():
    ws = _ws()  # never connected

    async def run():
        await ws.__anext__()

    with pytest.raises(Exception, match="not connected"):
        asyncio.run(run())


def test_anext_stops_iteration_when_disconnected_after_timeout():
    async def run():
        ws = _ws()
        ws._connected = True  # connected but queue empty and no socket
        # First wait_for times out; _connected flipped to False -> StopAsyncIteration.

        async def flip():
            await asyncio.sleep(0.05)
            ws._connected = False

        asyncio.create_task(flip())
        with pytest.raises(StopAsyncIteration):
            await ws.__anext__()

    asyncio.run(run())


def test_anext_returns_queued_message():
    async def run():
        ws = _ws()
        ws._connected = True
        ws._message_queue.put_nowait("hello")
        return await ws.__anext__()

    assert asyncio.run(run()) == "hello"


def test_is_connected_false_when_no_socket():
    assert _ws().is_connected is False


def test_is_connected_uses_closed_attr():
    ws = _ws()
    ws._connected = True
    ws._ws = type("W", (), {"closed": True})()
    assert ws.is_connected is False
    ws._ws = type("W", (), {"closed": False})()
    assert ws.is_connected is True


def test_is_connected_uses_state_when_no_closed_attr():
    ws = _ws()
    ws._connected = True
    ws._ws = type("W", (), {"state": type("S", (), {"name": "OPEN"})()})()
    assert ws.is_connected is True
    ws._ws = type("W", (), {"state": type("S", (), {"name": "CLOSED"})()})()
    assert ws.is_connected is False


# ---- connect: ws:// path + payload send failure -----------------------------


def test_connect_plain_ws_scheme(monkeypatch):
    """ws:// (non-TLS) base URL connects without an SSL context."""

    async def run():
        captured = {}

        async def fake_connect(url, **kwargs):
            captured["ssl"] = kwargs.get("ssl")
            return FakeAsyncWS()

        monkeypatch.setattr(_client_mod.websockets, "connect", fake_connect)
        ws = OrderFeedWebSocket(base_url="http://localhost:8080", auth="T", sid="S")
        await ws.connect()
        await ws.close()
        return captured

    captured = asyncio.run(run())
    assert captured["ssl"] is None  # no TLS context for ws://


def test_connect_payload_send_failure_wrapped(monkeypatch):
    async def run():
        class BadSendWS(FakeAsyncWS):
            async def send(self, data):
                raise RuntimeError("send failed")

        _patch_connect(monkeypatch, BadSendWS())
        ws = OrderFeedWebSocket(base_url="https://e21.x.com", auth="T", sid="S")
        await ws.connect()

    with pytest.raises(Exception, match="Failed to send connection payload"):
        asyncio.run(run())


# ---- receive loop callbacks -------------------------------------------------


def test_receive_loop_invokes_on_raw_and_on_message(monkeypatch):
    async def run():
        order = '{"type":"order","data":{"nOrdNo":"1","ordSt":"open"}}'
        ack = '{"ak":"ok","type":"cn","msg":"connected"}'
        fake = FakeAsyncWS(incoming=[ack, order])
        _patch_connect(monkeypatch, fake)

        raw_frames = []
        messages = []
        ws = OrderFeedWebSocket(base_url="https://e21.x.com", auth="T", sid="S")
        ws.on_raw = raw_frames.append
        ws.on_message = messages.append

        await ws.connect()
        # Give the receive loop time to process both frames.
        await asyncio.sleep(0.05)
        await ws.close()
        return raw_frames, messages

    raw_frames, messages = asyncio.run(run())
    # on_raw sees both frames (ack + order); on_message only the decoded order
    # (the ack is a control frame and is dropped).
    assert len(raw_frames) == 2
    assert len(messages) == 1
    assert isinstance(messages[0], OrderUpdate)


# ---- _parse_message edge cases ----------------------------------------------


def test_parse_bytes_json_frame():
    msg = _ws()._parse_message(b'{"type":"order","data":{"nOrdNo":"1"}}')
    assert isinstance(msg, OrderUpdate)
    assert msg.data.order_id == "1"


def test_parse_invalid_utf8_bytes_returned_as_is():
    bad = b"\xff\xfe\x00"
    assert _ws()._parse_message(bad) == bad


def test_parse_non_dict_json_returned_as_is():
    # Valid JSON but not an object (a list) -> returned as-is.
    assert _ws()._parse_message("[1, 2, 3]") == [1, 2, 3]


# ---- _handle_disconnect -----------------------------------------------------


def test_handle_disconnect_calls_on_disconnect_and_stops_at_cap(monkeypatch):
    async def run():
        async def always_fail(url, **kwargs):
            raise OSError("down")

        monkeypatch.setattr(_client_mod.websockets, "connect", always_fail)
        ws = OrderFeedWebSocket(
            base_url="https://e21.x.com",
            auth="T",
            sid="S",
            reconnect_delay=0,
            max_reconnect_attempts=2,
        )
        events = []
        errors = []
        ws.on_disconnect = lambda: events.append("disc")
        ws.on_error = errors.append
        ws._reconnect_count = 0
        await ws._handle_disconnect()
        return ws._reconnect_count, events, errors

    count, events, errors = asyncio.run(run())
    assert count == 2  # stopped at the cap
    assert len(events) >= 1  # on_disconnect fired
    assert len(errors) >= 1  # reconnect failures reported


def test_handle_disconnect_no_retry_when_cap_already_reached():
    async def run():
        ws = _ws()
        ws._reconnect_count = 5
        ws.max_reconnect_attempts = 2
        disc = []
        ws.on_disconnect = lambda: disc.append(1)
        await ws._handle_disconnect()
        return ws._reconnect_count, disc

    count, disc = asyncio.run(run())
    assert count == 5  # unchanged (no further attempts)
    assert disc == [1]


# ---- close ------------------------------------------------------------------


def test_close_when_never_connected_is_safe():
    async def run():
        ws = _ws()  # no socket, no receive task
        disc = []
        ws.on_disconnect = lambda: disc.append(1)
        await ws.close()
        return disc

    assert asyncio.run(run()) == [1]


def test_is_connected_true_when_socket_has_no_state_or_closed():
    ws = _ws()
    ws._connected = True
    ws._ws = object()  # no `closed`, no `state` attribute -> assumed open
    assert ws.is_connected is True


def test_anext_recurses_after_timeout_then_returns_message():
    async def run():
        ws = _ws()
        ws._connected = True

        async def deliver():
            await asyncio.sleep(1.2)  # force one wait_for timeout first
            ws._message_queue.put_nowait("late")

        asyncio.create_task(deliver())
        return await ws.__anext__()

    assert asyncio.run(run()) == "late"


def test_handle_disconnect_retry_without_on_error_callback(monkeypatch):
    async def run():
        async def always_fail(url, **kwargs):
            raise OSError("down")

        monkeypatch.setattr(_client_mod.websockets, "connect", always_fail)
        ws = OrderFeedWebSocket(
            base_url="https://e21.x.com",
            auth="T",
            sid="S",
            reconnect_delay=0,
            max_reconnect_attempts=1,
        )
        # on_error deliberately left as None -> exercises the 277->279 arc.
        await ws._handle_disconnect()
        return ws._reconnect_count

    assert asyncio.run(run()) == 1


def test_parse_dict_input_passed_through_as_order():
    # A frame already decoded to a dict (not str/bytes) is handled directly.
    msg = _ws()._parse_message({"type": "order", "data": {"nOrdNo": "9"}})
    assert isinstance(msg, OrderUpdate)
    assert msg.data.order_id == "9"


def test_receive_loop_exits_when_connection_flips_closed():
    async def run():
        class OneShotWS(FakeAsyncWS):
            async def recv(self):
                # Deliver one frame, then mark the socket closed so the loop's
                # `while self.is_connected` guard exits normally (no exception).
                self.closed = True
                return '{"type":"order","data":{"nOrdNo":"1"}}'

        ws = _ws()
        fake = OneShotWS()
        ws._ws = fake
        ws._connected = True
        await ws._receive_loop()
        # The single frame was still enqueued before the loop exited.
        return ws._message_queue.qsize()

    assert asyncio.run(run()) == 1


# ---- TLS verification -------------------------------------------------------


def test_connect_verifies_tls_by_default(monkeypatch):
    """Default connect() uses a cert-verifying SSL context for wss://."""

    async def run():
        captured = {}

        async def fake_connect(url, **kwargs):
            captured["ssl"] = kwargs.get("ssl")
            return FakeAsyncWS()

        monkeypatch.setattr(_client_mod.websockets, "connect", fake_connect)
        ws = OrderFeedWebSocket(base_url="https://e21.x.com", auth="T", sid="S")
        await ws.connect()
        await ws.close()
        return captured["ssl"]

    ctx = asyncio.run(run())
    import ssl as _ssl

    assert ctx is not None
    assert ctx.verify_mode == _ssl.CERT_REQUIRED
    assert ctx.check_hostname is True


def test_connect_verify_ssl_false_disables_and_warns(monkeypatch):
    """verify_ssl=False disables verification and emits a warning."""

    async def run():
        captured = {}

        async def fake_connect(url, **kwargs):
            captured["ssl"] = kwargs.get("ssl")
            return FakeAsyncWS()

        monkeypatch.setattr(_client_mod.websockets, "connect", fake_connect)
        ws = OrderFeedWebSocket(base_url="https://e21.x.com", auth="T", sid="S", verify_ssl=False)
        await ws.connect()
        await ws.close()
        return captured["ssl"]

    import ssl as _ssl

    with pytest.warns(UserWarning, match="man-in-the-middle"):
        ctx = asyncio.run(run())

    assert ctx.verify_mode == _ssl.CERT_NONE
    assert ctx.check_hostname is False
