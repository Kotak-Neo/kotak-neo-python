"""Unit tests for the SFeed native_batch binary protocol decoder."""

import struct

import pytest

# The feed subpackage imports the client, which needs `websockets` (a core
# dependency). Guard defensively so the module skips rather than errors if it is
# somehow missing from the environment.
pytest.importorskip("websockets")

from neo_api_client.websocket.feed.models import (  # noqa: E402
    SFeedCasChange,
    SFeedIndex,
    SFeedMarketStatus,
    SFeedScrip,
    SFeedScripLite,
    WsToken,
)
from neo_api_client.websocket.feed.protocol import (  # noqa: E402
    HEADER_SIZE,
    MSG_CAS_CHANGE,
    MSG_INDEX,
    MSG_MARKET_CLOSE,
    MSG_MARKET_OPEN,
    MSG_MARKET_PICTURE,
    MSG_MARKET_STATUS,
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
_MARKET_STATUS_BODY = struct.Struct("<H5s")
_CAS_CHANGE_BODY = struct.Struct("<IIqq")


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


def _market_status_packet(status_code=3, status=b"CLOSE"):
    body = _MARKET_STATUS_BODY.pack(status_code, status)
    length = HEADER_SIZE + len(body)
    return _header(length, MSG_MARKET_STATUS, level=0) + body


def _cas_change_packet(
    stk_exch_token=1333, ref_price=72005, imbalance_qty=0, imbalance_qty_at_market=0
):
    body = _CAS_CHANGE_BODY.pack(stk_exch_token, ref_price, imbalance_qty, imbalance_qty_at_market)
    length = HEADER_SIZE + len(body)
    return _header(length, MSG_CAS_CHANGE, level=0) + body


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


def _market_picture_packet(level=4, buy_n=1, sell_n=1, last_update_time=1234567891):
    body = _MP_BODY.pack(
        11536,  # token
        1000,  # total_buy_qty
        2000,  # total_sell_qty
        50000,  # volume_traded_today
        1234567890,  # last_trade_time
        last_update_time,
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


def test_decode_market_status():
    """message_code 105 (sent via subscribe_exchange()) decodes to the same
    SFeedMarketStatus model as 6511/6521. status is looked up from the
    static MARKET_STATUS_TEXT mapping by status_code, NOT the raw wire
    string -- the wire string is unreliable (often blank on the live feed)."""
    msg = decode_packet(_market_status_packet(status_code=2, status=b"CLOSE"), DIVIDERS)
    assert isinstance(msg, SFeedMarketStatus)
    assert msg.exchange_segment == "nse_cm"
    assert not hasattr(msg, "instrument_token")
    assert msg.status_code == 2
    assert msg.status == "Market closed"


def test_decode_market_status_open():
    msg = decode_packet(_market_status_packet(status_code=1, status=b"OPEN\x00"), DIVIDERS)
    assert msg.status_code == 1
    assert msg.status == "Market open"


def test_decode_market_status_ignores_wire_string_when_code_is_known():
    """Even a populated (non-empty) wire status string is ignored in favor
    of the static mapping when status_code is one of the 12 known codes --
    the mapping is the source of truth, not whatever the wire happens to
    contain (which the live feed shows is often blank anyway)."""
    msg = decode_packet(_market_status_packet(status_code=5, status=b"AUCTN"), DIVIDERS)
    assert msg.status_code == 5
    assert msg.status == "Auction status changed"


def test_decode_market_status_unknown_code_falls_back_to_wire_string():
    """A status_code NOT in the static mapping (e.g. a future 13th code)
    falls back to whatever the wire actually sent, rather than raising or
    silently losing information."""
    msg = decode_packet(_market_status_packet(status_code=99, status=b"XYZ\x00\x00"), DIVIDERS)
    assert msg.status_code == 99
    assert msg.status == "XYZ"


def test_decode_market_status_unknown_code_and_blank_wire_string():
    """A status_code NOT in the static mapping, with also nothing usable on
    the wire, falls back to a placeholder instead of an empty string."""
    msg = decode_packet(
        _market_status_packet(status_code=99, status=b"\x00\x00\x00\x00\x00"), DIVIDERS
    )
    assert msg.status == "Unknown status_code 99"


def test_decode_cas_change():
    """message_code 104: per-instrument CAS reference-price/imbalance
    update. Delivered on subscribe_scrips()/subscribe_depth(), not a
    separate subscription -- has a real instrument_token, unlike
    SFeedMarketStatus."""
    msg = decode_packet(
        _cas_change_packet(
            stk_exch_token=1333,
            ref_price=72005,
            imbalance_qty=1500,
            imbalance_qty_at_market=250,
        ),
        DIVIDERS,
    )
    assert isinstance(msg, SFeedCasChange)
    assert msg.exchange_segment == "nse_cm"
    assert msg.instrument_token == "1333"
    assert msg.ref_price == pytest.approx(720.05)  # 72005 / 100
    assert msg.imbalance_qty == 1500
    assert msg.imbalance_qty_at_market == 250
    assert msg.trading_symbol is None  # not yet resolved from a subscribe ack


def test_decode_cas_change_negative_imbalance_qty():
    """imbalance_qty/imbalance_qty_at_market are signed 64-bit (like every
    other quantity field in this protocol, e.g. total_buy_qty) -- a negative
    value must round-trip, not get misread as a huge unsigned number."""
    msg = decode_packet(
        _cas_change_packet(imbalance_qty=-500, imbalance_qty_at_market=-10),
        DIVIDERS,
    )
    assert msg.imbalance_qty == -500
    assert msg.imbalance_qty_at_market == -10


def test_decode_cas_change_all_zero_dropped():
    """Outside the CAS window, the exchange still broadcasts this packet but
    with ref_price/imbalance_qty/imbalance_qty_at_market all zero -- carries
    no real information, so it's dropped (decode_packet returns None)
    rather than delivering a meaningless message."""
    msg = decode_packet(
        _cas_change_packet(ref_price=0, imbalance_qty=0, imbalance_qty_at_market=0),
        DIVIDERS,
    )
    assert msg is None


def test_decode_cas_change_not_dropped_when_only_some_fields_are_zero():
    """Only dropped when ALL THREE of ref_price/imbalance_qty/
    imbalance_qty_at_market are zero -- a real CAS update can legitimately
    have some (but not all) of these at zero, and must still be delivered."""
    msg = decode_packet(
        _cas_change_packet(ref_price=72005, imbalance_qty=0, imbalance_qty_at_market=0),
        DIVIDERS,
    )
    assert msg is not None
    assert msg.ref_price == pytest.approx(720.05)

    msg = decode_packet(
        _cas_change_packet(ref_price=0, imbalance_qty=100, imbalance_qty_at_market=0),
        DIVIDERS,
    )
    assert msg is not None
    assert msg.imbalance_qty == 100

    msg = decode_packet(
        _cas_change_packet(ref_price=0, imbalance_qty=0, imbalance_qty_at_market=50),
        DIVIDERS,
    )
    assert msg is not None
    assert msg.imbalance_qty_at_market == 50


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


def test_decode_market_picture_normalizes_negative_last_update_time():
    """A never-updated instrument sends last_update_time as a negative
    sentinel (e.g. -2209008600, which is 1900-01-01 00:00:00 IST expressed
    as a signed Unix timestamp) rather than 0 like last_trade_time uses for
    the same "no value yet" case -- normalized to 0 to match."""
    msg = decode_packet(_market_picture_packet(last_update_time=-2209008600), DIVIDERS)
    assert msg.last_update_time == 0


def test_decode_market_picture_keeps_non_negative_last_update_time():
    """A real (non-negative) last_update_time must pass through unchanged."""
    msg = decode_packet(_market_picture_packet(last_update_time=1234567891), DIVIDERS)
    assert msg.last_update_time == 1234567891


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
    """No body on 6511/6521 -- status_code is synthesized to line up with
    MarketStatusCode.BCAST_OPEN_MESSAGE/BCAST_CLOSE_MESSAGE (1/2), and status
    is the same static MARKET_STATUS_TEXT used by message_code 105, so both
    paths produce identical text for the same status_code."""
    open_pkt = _header(HEADER_SIZE, MSG_MARKET_OPEN)
    close_pkt = _header(HEADER_SIZE, MSG_MARKET_CLOSE)
    om = decode_packet(open_pkt, DIVIDERS)
    cm = decode_packet(close_pkt, DIVIDERS)
    assert isinstance(om, SFeedMarketStatus)
    assert om.status_code == 1
    assert om.status == "Market open"
    assert isinstance(cm, SFeedMarketStatus)
    assert cm.status_code == 2
    assert cm.status == "Market closed"


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
