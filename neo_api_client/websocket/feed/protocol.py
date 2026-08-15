"""Binary wire-protocol decoding for the SFeed ``native_batch`` feed.

The data plane is little-endian, packed (``#pragma pack(1)``), and batched:
one WebSocket binary frame may carry several packets laid end to end. Each
packet begins with a ``uint16`` length prefix and a 9-byte common header.

See the SFeed Feed Data Documentation (native_batch) for the wire layout.
"""

import struct

from neo_api_client.websocket.feed.models import (
    EXCHANGE_ID_TO_NAME,
    DepthLevel,
    Level,
    SFeedIndex,
    SFeedMarketStatus,
    SFeedScrip,
    SFeedScripLite,
)

HEADER_SIZE = 9
DEFAULT_DIVIDER = 100

# Message codes (uint16 LE at header offset 2)
# Auth responses observed: 1117 (documented) and 1119 (SFeed production).
MSG_AUTH_RESPONSE = 1117
MSG_AUTH_RESPONSE_CODES = (1117, 1119)
# Subscribe acknowledgement (JSON control frame) carrying the trading_symbols
# map. Sent when the subscribe request includes "ack_symbol": true.
MSG_SUBSCRIBE_ACK = 1109
MSG_MARKET_OPEN = 6511
MSG_MARKET_CLOSE = 6521
MSG_INDEX = 7207
MSG_MARKET_PICTURE = 7208

# Struct layouts (all little-endian, packed). Bodies start at HEADER_SIZE (@9).
# Header: message_length u16, message_code u16, exchange_id i8, level u8,
#         auction_flag u8, seq_no u8, bitmask_length u8  => 9 bytes
_HEADER = struct.Struct("<HHbBBBB")
_U16 = struct.Struct("<H")

# IndexMessage body (@9): token, open, close, high, low, index_value,
#   last_trade_time(u64), yearly_high, yearly_low, net_chg_percent,
#   _market_cap(f64), precision(u8), multiplier, name[21]
_INDEX_BODY = struct.Struct("<IiiiiiQiiidBi21s")

# MiniTouchLine body (@9): token, last_trade_time(i64), last_traded_price,
#   last_trade_qty(i64), close_price, net_chg_percent, net_chg, market_lot,
#   precision(u8), multiplier  => 45 bytes (total packet 54)
_MINI_BODY = struct.Struct("<IqIqIiiIBI")

# MarketPicture fixed body (@9 .. @144): 135 bytes, followed by DepthRows.
_MP_BODY = struct.Struct("<IqqqqqIIIIIqIIIIhiIdiIIIIIBI")
_MP_FIXED_END = 144

# DepthRow: qty(i64), price(i32), number_of_orders(i32)  => 16 bytes
_DEPTH_ROW = struct.Struct("<qii")
_DEPTH_ROW_SIZE = 16


def split_batch(frame: bytes) -> list[bytes]:
    """Split a batched binary frame into individual packets.

    Reads the ``uint16`` length prefix of each packet, slices it out, and
    advances. Stops on a truncated tail rather than raising.
    """
    packets: list[bytes] = []
    offset = 0
    n = len(frame)
    while offset + 2 <= n:
        size = _U16.unpack_from(frame, offset)[0]
        if size < HEADER_SIZE or offset + size > n:
            break  # zero/garbage length or truncated tail
        packets.append(frame[offset : offset + size])
        offset += size
    return packets


def _decode_string(raw: bytes) -> str:
    """Decode a fixed-size, NUL-padded UTF-8 string field."""
    return raw.split(b"\x00", 1)[0].decode("utf-8", "replace").strip()


def decode_packet(packet: bytes, dividers: dict[int, int]):
    """Decode one de-framed packet into a feed message, or None to ignore.

    Args:
        packet: A single packet (header + body), already sliced from a batch.
        dividers: Map of exchange_id -> price divider (from the auth response).

    Returns:
        An SFeed* message, or None for unknown / unsupported packets.
    """
    if len(packet) < HEADER_SIZE:
        return None

    (
        message_length,
        message_code,
        exchange_id,
        level,
        auction_flag,
        _seq_no,
        _bitmask_length,
    ) = _HEADER.unpack_from(packet, 0)

    exchange = EXCHANGE_ID_TO_NAME.get(exchange_id, str(exchange_id))
    divider = dividers.get(exchange_id) or DEFAULT_DIVIDER

    # Route by message_code first (per spec), then fall back to level.
    if message_code in (MSG_MARKET_OPEN, MSG_MARKET_CLOSE):
        # instrument_token is empty here (market-status frames carry no token);
        # it is not a credential despite bandit's password heuristic.
        return SFeedMarketStatus(
            exchange_segment=exchange,
            instrument_token="",  # nosec B106
            status="open" if message_code == MSG_MARKET_OPEN else "close",
        )

    if message_code == MSG_INDEX:
        return _decode_index(packet, exchange, divider)

    # Market-data packets are routed by the level byte (not message_code).
    if level == Level.MINI_TOUCH_LINE:
        return _decode_mini(packet, exchange, divider)
    if level in (2, Level.TOUCH_LINE, Level.DEPTH, Level.FULL_DEPTH):
        return _decode_market_picture(
            packet, exchange, divider, int(level), auction_flag, message_length
        )

    return None


def _decode_index(packet: bytes, exchange: str, divider: int) -> SFeedIndex:
    (
        token,
        open_price,
        close_price,
        high_price,
        low_price,
        index_value,
        last_trade_time,
        yearly_high,
        yearly_low,
        net_chg_percent,
        _market_cap,
        precision,
        multiplier,
        name,
    ) = _INDEX_BODY.unpack_from(packet, HEADER_SIZE)

    return SFeedIndex(
        exchange_segment=exchange,
        instrument_token=str(token),
        name=_decode_string(name),
        last_traded_price=index_value / divider,
        open_price=open_price / divider,
        high_price=high_price / divider,
        low_price=low_price / divider,
        close_price=close_price / divider,
        change=(index_value - close_price) / divider,
        net_change_percent=net_chg_percent / 100,
        yearly_high=yearly_high / divider,
        yearly_low=yearly_low / divider,
        last_trade_time=last_trade_time,
        precision=precision,
        multiplier=multiplier / divider,
    )


def _decode_mini(packet: bytes, exchange: str, divider: int) -> SFeedScripLite:
    (
        token,
        last_trade_time,
        last_traded_price,
        last_trade_qty,
        close_price,
        net_chg_percent,
        net_chg,
        market_lot,
        precision,
        multiplier,
    ) = _MINI_BODY.unpack_from(packet, HEADER_SIZE)

    return SFeedScripLite(
        exchange_segment=exchange,
        instrument_token=str(token),
        last_traded_price=last_traded_price / divider,
        last_trade_time=last_trade_time,
        last_trade_qty=last_trade_qty,
        close_price=close_price / divider,
        net_change=net_chg / divider,
        net_change_percent=net_chg_percent / 100,
        market_lot=market_lot,
        precision=precision,
        multiplier=multiplier,
    )


def _decode_market_picture(
    packet: bytes,
    exchange: str,
    divider: int,
    level: int,
    auction_flag: int,
    message_length: int,
) -> SFeedScrip:
    (
        token,
        total_buy_qty,
        total_sell_qty,
        volume_traded_today,
        last_trade_time,
        last_update_time,
        open_price,
        close_price,
        high_price,
        low_price,
        last_traded_price,
        last_trade_qty,
        avg_trade_price,
        _indicative_close,
        buy_depth_count,
        sell_depth_count,
        _trading_status,
        net_chg_percent,
        open_interest,
        total_traded_value,
        net_chg,
        upper_circuit,
        lower_circuit,
        yearly_high,
        yearly_low,
        market_lot,
        precision,
        multiplier,
    ) = _MP_BODY.unpack_from(packet, HEADER_SIZE)

    # Touch line (level 4) always carries exactly 1 bid + 1 ask.
    if level == Level.TOUCH_LINE:
        buy_n, sell_n = 1, 1
    else:
        buy_n, sell_n = buy_depth_count, sell_depth_count

    buy: list[DepthLevel] = []
    sell: list[DepthLevel] = []
    offset = _MP_FIXED_END
    limit = min(message_length, len(packet))
    total_rows = buy_n + sell_n
    for i in range(total_rows):
        if offset + _DEPTH_ROW_SIZE > limit:
            break  # packet carried fewer rows than the counts imply
        qty, price, orders = _DEPTH_ROW.unpack_from(packet, offset)
        row = DepthLevel(quantity=qty, price=price / divider, orders=orders)
        (buy if i < buy_n else sell).append(row)
        offset += _DEPTH_ROW_SIZE

    return SFeedScrip(
        exchange_segment=exchange,
        instrument_token=str(token),
        level=level,
        last_traded_price=last_traded_price / divider,
        open_price=open_price / divider,
        high_price=high_price / divider,
        low_price=low_price / divider,
        close_price=close_price / divider,
        average_trade_price=avg_trade_price / divider,
        last_trade_time=last_trade_time,
        last_update_time=last_update_time,
        last_trade_qty=last_trade_qty,
        total_buy_quantity=total_buy_qty,
        total_sell_quantity=total_sell_qty,
        volume_traded_today=volume_traded_today,
        open_interest=open_interest,
        net_change=net_chg / divider,
        net_change_percent=net_chg_percent / 100,
        upper_circuit_limit=upper_circuit / divider,
        lower_circuit_limit=lower_circuit / divider,
        yearly_high=yearly_high / divider,
        yearly_low=yearly_low / divider,
        total_traded_value=total_traded_value / divider,
        market_lot=market_lot,
        precision=precision,
        multiplier=multiplier,
        auction=auction_flag > 0,
        buy=buy,
        sell=sell,
    )
