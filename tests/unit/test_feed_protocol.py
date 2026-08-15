"""Unit tests for the SFeed native_batch binary protocol decoder."""

import struct

import pytest

# The feed subpackage imports the client, which needs `websockets` (a core
# dependency). Guard defensively so the module skips rather than errors if it is
# somehow missing from the environment.
pytest.importorskip("websockets")

from neo_api_client.websocket.feed.models import (  # noqa: E402
    SFeedIndex,
    SFeedMarketStatus,
    SFeedScrip,
    SFeedScripLite,
    WsToken,
)
from neo_api_client.websocket.feed.protocol import (  # noqa: E402
    HEADER_SIZE,
    MSG_INDEX,
    MSG_MARKET_CLOSE,
    MSG_MARKET_OPEN,
    MSG_MARKET_PICTURE,
    decode_packet,
    split_batch,
)

NSE_CM = 1  # exchange_id
DIVIDERS = {NSE_CM: 100}

_HEADER = struct.Struct("<HHbBBBB")
_INDEX_BODY = struct.Struct("<IiiiiiQiiidBi21s")
_MINI_BODY = struct.Struct("<IqIqIiiIBI")
_MP_BODY = struct.Struct("<IqqqqqIIIIIqIIIIhiIdiIIIIIBI")
_DEPTH_ROW = struct.Struct("<qii")


def _header(message_length, message_code, exchange_id=NSE_CM, level=0, auction=0):
    return _HEADER.pack(message_length, message_code, exchange_id, level, auction, 0, 0)


def _index_packet():
    body = _INDEX_BODY.pack(
        26000,  # token
        2000000,  # open  -> 20000.00
        1990000,  # close -> 19900.00
        2010000,  # high
        1980000,  # low
        2005000,  # index_value -> 20050.00
        1234567890,  # last_trade_time
        2100000,  # yearly_high
        1500000,  # yearly_low
        150,  # net_chg_percent -> 1.50
        0.0,  # _market_cap
        2,  # precision
        100,  # multiplier
        b"NIFTY 50",  # name
    )
    length = HEADER_SIZE + len(body)
    return _header(length, MSG_INDEX, level=0) + body


def _mini_packet():
    body = _MINI_BODY.pack(
        11536,  # token
        1234567890,  # last_trade_time
        150050,  # last_traded_price -> 1500.50
        10,  # last_trade_qty
        149900,  # close_price (NOT divided -> stays 149900.0)
        123,  # net_chg_percent -> 1.23
        150,  # net_chg -> 1.50
        1,  # market_lot
        2,  # precision
        1,  # multiplier
    )
    length = HEADER_SIZE + len(body)  # 9 + 45 = 54
    return _header(length, MSG_MARKET_PICTURE, level=1) + body


def _market_picture_packet(level=4, buy_n=1, sell_n=1):
    body = _MP_BODY.pack(
        11536,  # token
        1000,  # total_buy_qty
        2000,  # total_sell_qty
        50000,  # volume_traded_today
        1234567890,  # last_trade_time
        1234567891,  # last_update_time
        150000,  # open_price -> 1500.00
        149000,  # close_price -> 1490.00
        151000,  # high_price
        148000,  # low_price
        150050,  # last_traded_price -> 1500.50
        10,  # last_trade_qty
        150025,  # avg_trade_price
        0,  # _indicative_close
        buy_n,  # buy_depth_count
        sell_n,  # sell_depth_count
        0,  # _trading_status
        123,  # net_chg_percent -> 1.23
        500,  # open_interest
        1234567.0,  # total_traded_value
        105,  # net_chg -> 1.05
        165000,  # upper_circuit
        135000,  # lower_circuit
        200000,  # yearly_high
        100000,  # yearly_low
        1,  # market_lot
        2,  # precision
        1,  # multiplier
    )
    # Pad fixed body to 144 - HEADER_SIZE, then append depth rows.
    fixed = body.ljust(144 - HEADER_SIZE, b"\x00")
    rows = b""
    for i in range(buy_n + sell_n):
        rows += _DEPTH_ROW.pack(100 + i, 150000 + i * 100, 5 + i)
    payload = fixed + rows
    length = HEADER_SIZE + len(payload)
    return _header(length, MSG_MARKET_PICTURE, level=level) + payload


def test_split_batch_single_packet():
    pkt = _mini_packet()
    packets = split_batch(pkt)
    assert len(packets) == 1
    assert packets[0] == pkt


def test_split_batch_multiple_packets():
    a, b = _mini_packet(), _index_packet()
    packets = split_batch(a + b)
    assert len(packets) == 2
    assert packets[0] == a
    assert packets[1] == b


def test_split_batch_truncated_tail_ignored():
    good = _mini_packet()
    packets = split_batch(good + b"\x99\x99\x02")  # bogus/short trailing bytes
    assert len(packets) == 1
    assert packets[0] == good


def test_decode_index():
    msg = decode_packet(_index_packet(), DIVIDERS)
    assert isinstance(msg, SFeedIndex)
    assert msg.exchange_segment == "nse_cm"
    assert msg.instrument_token == "26000"
    assert msg.name == "NIFTY 50"
    assert msg.last_traded_price == pytest.approx(20050.0)
    assert msg.close_price == pytest.approx(19900.0)
    # change = index_value - close_price, scaled
    assert msg.change == pytest.approx(20050.0 - 19900.0)
    assert msg.net_change_percent == pytest.approx(1.50)


def test_decode_mini_touch_line():
    msg = decode_packet(_mini_packet(), DIVIDERS)
    assert isinstance(msg, SFeedScripLite)
    assert msg.instrument_token == "11536"
    assert msg.last_traded_price == pytest.approx(1500.50)
    assert msg.net_change == pytest.approx(1.50)
    assert msg.net_change_percent == pytest.approx(1.23)


def test_mini_touch_line_close_price_scaled():
    """close_price is scaled by the exchange divider, like every other price field."""
    msg = decode_packet(_mini_packet(), DIVIDERS)
    assert msg.close_price == pytest.approx(1499.00)  # 149900 / 100


def test_decode_market_picture_touch_line():
    msg = decode_packet(_market_picture_packet(level=4, buy_n=1, sell_n=1), DIVIDERS)
    assert isinstance(msg, SFeedScrip)
    assert msg.level == 4
    assert msg.last_traded_price == pytest.approx(1500.50)
    assert msg.open_price == pytest.approx(1500.00)
    assert len(msg.buy) == 1
    assert len(msg.sell) == 1
    assert msg.buy[0].price == pytest.approx(1500.00)


def test_touch_line_forces_one_bid_one_ask():
    """level == 4 must read exactly 1 bid + 1 ask regardless of counts."""
    # Body claims 5+5 rows but only 2 rows worth of data present.
    pkt = _market_picture_packet(level=4, buy_n=5, sell_n=5)
    # Trim so only 2 depth rows exist after the fixed body.
    trimmed = pkt[: 144 + 2 * 16]
    trimmed = struct.pack("<H", len(trimmed)) + trimmed[2:]  # fix message_length
    msg = decode_packet(trimmed, DIVIDERS)
    assert len(msg.buy) == 1
    assert len(msg.sell) == 1


def test_decode_full_depth_multiple_rows():
    msg = decode_packet(_market_picture_packet(level=16, buy_n=3, sell_n=2), DIVIDERS)
    assert msg.level == 16
    assert len(msg.buy) == 3
    assert len(msg.sell) == 2


def test_depth_stops_when_packet_has_fewer_rows_than_counts():
    """Depth loop breaks early when the packet carries fewer rows than the
    declared buy/sell counts imply (protocol.py line 251)."""
    # Claims 3 buy + 2 sell = 5 rows, but trim so only 2 rows are present.
    pkt = _market_picture_packet(level=16, buy_n=3, sell_n=2)
    trimmed = pkt[: 144 + 2 * 16]  # keep the fixed body + only 2 depth rows
    trimmed = struct.pack("<H", len(trimmed)) + trimmed[2:]  # fix message_length
    msg = decode_packet(trimmed, DIVIDERS)
    # Only 2 rows could be read before the loop hit the break; both are bids
    # (i < buy_n for i in 0,1), so no sell rows were parsed.
    assert len(msg.buy) == 2
    assert len(msg.sell) == 0


def test_decode_market_open_close():
    open_pkt = _header(HEADER_SIZE, MSG_MARKET_OPEN)
    close_pkt = _header(HEADER_SIZE, MSG_MARKET_CLOSE)
    om = decode_packet(open_pkt, DIVIDERS)
    cm = decode_packet(close_pkt, DIVIDERS)
    assert isinstance(om, SFeedMarketStatus) and om.status == "open"
    assert isinstance(cm, SFeedMarketStatus) and cm.status == "close"


def test_default_divider_when_exchange_missing():
    """Unknown exchange_id falls back to divider 100."""
    msg = decode_packet(_index_packet(), {})  # no dividers supplied
    assert msg.last_traded_price == pytest.approx(20050.0)


def test_unknown_packet_ignored():
    # message_code that isn't index/open/close and level 0 -> ignored
    pkt = _header(HEADER_SIZE, 9999, level=0)
    assert decode_packet(pkt, DIVIDERS) is None


def test_short_packet_ignored():
    assert decode_packet(b"\x00\x01", DIVIDERS) is None


def test_wstoken_inputtoken():
    assert WsToken("nse_cm", "11536").inputtoken == "nse_cm|11536"
