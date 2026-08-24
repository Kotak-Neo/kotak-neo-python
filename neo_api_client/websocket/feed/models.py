"""Pydantic models for SFeed WebSocket feed messages (native_batch).

Field values here are already decoded and scaled (prices divided by the
per-exchange divider, net_chg_percent divided by 100) by
:mod:`neo_api_client.websocket.feed.protocol`.
"""

from enum import IntEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


# Market status codes (SFeedMarketStatus.status_code body, message_code 105),
# from the WebSocket team.
class MarketStatusCode(IntEnum):
    BCAST_OPEN_MESSAGE = 1
    BCAST_CLOSE_MESSAGE = 2
    BCAST_PREOPEN_SHUTDOWN_MSG = 3
    BCAST_NORMAL_MKT_PREOPEN_ENDED = 4
    BCAST_AUCTION_STATUS_CHANGE = 5
    BCAST_CLOSING_START = 6
    BCAST_CLOSING_END = 7
    BCAST_CTS_CLOSE_FOR_CAS = 8
    BCAST_REVISED_PRICE_BAND_COMPLETED = 9
    BCAST_CAS_START = 10
    BCAST_MARKET_ORDER_RESTRICTED = 11
    BCAST_CAS_END = 12


# Static, human-readable text per MarketStatusCode, from the WebSocket team.
# Used instead of the raw wire status string, which is unreliable -- e.g. the
# live feed sends an empty string for status_code 2 (BCAST_CLOSE_MESSAGE) on
# most segments, not "CLOSE".
MARKET_STATUS_TEXT: dict[int, str] = {
    MarketStatusCode.BCAST_OPEN_MESSAGE: "Market open",
    MarketStatusCode.BCAST_CLOSE_MESSAGE: "Market closed",
    MarketStatusCode.BCAST_PREOPEN_SHUTDOWN_MSG: "Pre-open session ending",
    MarketStatusCode.BCAST_NORMAL_MKT_PREOPEN_ENDED: "Pre-open ended, normal market open",
    MarketStatusCode.BCAST_AUCTION_STATUS_CHANGE: "Auction status changed",
    MarketStatusCode.BCAST_CLOSING_START: "Closing session started",
    MarketStatusCode.BCAST_CLOSING_END: "Closing session ended",
    MarketStatusCode.BCAST_CTS_CLOSE_FOR_CAS: (
        "Continuous trading closed, closing auction starting soon"
    ),
    MarketStatusCode.BCAST_REVISED_PRICE_BAND_COMPLETED: "Closing auction price band set",
    MarketStatusCode.BCAST_CAS_START: "Closing auction (CAS) started",
    MarketStatusCode.BCAST_MARKET_ORDER_RESTRICTED: "Market orders restricted",
    MarketStatusCode.BCAST_CAS_END: "Closing auction (CAS) ended",
}


# Exchange enum — transmitted as a signed byte (exchange_id) in binary headers,
# and as a name string in the JSON control plane.
class Exchange(IntEnum):
    NONE = 0
    NSE_CM = 1
    NSE_FO = 2
    CDE_FO = 3
    NSE_COM = 4
    BSE_CM = 5
    BSE_FO = 6
    BSE_CD = 7
    BSE_CO = 8
    MCX_FO = 9
    NCD_CO = 10


# Wire name <-> enum id maps.
EXCHANGE_NAME_TO_ID: dict[str, int] = {
    "none": Exchange.NONE,
    "nse_cm": Exchange.NSE_CM,
    "nse_fo": Exchange.NSE_FO,
    "cde_fo": Exchange.CDE_FO,
    "nse_com": Exchange.NSE_COM,
    "bse_cm": Exchange.BSE_CM,
    "bse_fo": Exchange.BSE_FO,
    "bse_cd": Exchange.BSE_CD,
    "bse_co": Exchange.BSE_CO,
    "mcx_fo": Exchange.MCX_FO,
    "ncd_co": Exchange.NCD_CO,
}
EXCHANGE_ID_TO_NAME: dict[int, str] = {v: k for k, v in EXCHANGE_NAME_TO_ID.items()}


# Level (depth) — transmitted as a u8 in the binary header.
class Level(IntEnum):
    MINI_TOUCH_LINE = 1
    TOUCH_LINE = 4
    DEPTH = 8
    FULL_DEPTH = 16


class WsToken(BaseModel):
    """WebSocket subscription token.

    Args:
        exchange_segment: Exchange segment string (e.g. 'nse_cm', 'mcx_fo').
        instrument_token: Instrument token / scrip code.

    Example:
        ```python
        WsToken("nse_cm", "11536")
        WsToken("mcx_fo", "499095")
        ```
    """

    # Immutable so a WsToken can be used as a dict key / set member.
    model_config = ConfigDict(frozen=True)

    exchange_segment: str = Field(..., description="Exchange segment")
    instrument_token: str = Field(..., description="Instrument token")

    def __init__(self, exchange_segment: str, instrument_token: str):
        super().__init__(exchange_segment=exchange_segment, instrument_token=instrument_token)

    @property
    def inputtoken(self) -> str:
        """The ``<exchange>|<token>`` form used in control-plane messages."""
        return f"{self.exchange_segment}|{self.instrument_token}"


class SFeedBase(BaseModel):
    """Base for all decoded feed messages."""

    exchange_segment: str
    instrument_token: str


class SFeedInstrumentMessage(SFeedBase):
    """Base for messages tied to a specific subscribed instrument.

    Adds trading_symbol, resolved from the subscribe acknowledgement
    (message_code 1109) and attached by the client -- None until the mapping
    is known for this token. Not used by SFeedMarketStatus, which has no
    specific instrument to resolve (instrument_token is always "").
    """

    trading_symbol: str | None = None


class DepthLevel(BaseModel):
    """A single market-depth row (bid or ask)."""

    quantity: int
    price: float
    orders: int


class SFeedScrip(SFeedInstrumentMessage):
    """Market picture (touch line / depth / full depth) — level in {2,4,8,16}."""

    type: Literal["scrip"] = "scrip"
    level: int
    last_traded_price: float
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    average_trade_price: float
    last_trade_time: int
    last_update_time: int
    last_trade_qty: int
    total_buy_quantity: int
    total_sell_quantity: int
    volume_traded_today: int
    open_interest: int
    net_change: float
    net_change_percent: float
    upper_circuit_limit: float
    lower_circuit_limit: float
    yearly_high: float
    yearly_low: float
    total_traded_value: float
    market_lot: int
    precision: int
    multiplier: int
    auction: bool = False
    buy: list[DepthLevel] = Field(default_factory=list)
    sell: list[DepthLevel] = Field(default_factory=list)


class SFeedScripLite(SFeedInstrumentMessage):
    """Mini touch line — level == 1."""

    type: Literal["scrip_lite"] = "scrip_lite"
    last_traded_price: float
    last_trade_time: int
    last_trade_qty: int
    close_price: float
    net_change: float
    net_change_percent: float
    market_lot: int
    precision: int
    multiplier: int


class SFeedIndex(SFeedInstrumentMessage):
    """Index message — message_code == 7207."""

    type: Literal["index"] = "index"
    name: str
    last_traded_price: float
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    change: float
    net_change_percent: float
    yearly_high: float
    yearly_low: float
    last_trade_time: int
    precision: int
    multiplier: float


class SFeedMarketStatus(BaseModel):
    """Market status notification.

    Stands apart from SFeedBase/SFeedInstrumentMessage on purpose: the wire
    packet for this message type carries no instrument token at all (only
    exchange_segment + status_code + status), so there's no instrument_token
    or trading_symbol field here -- only what the feed actually sends.

    Delivered from message_code 105 (has a real body -- ``status_code`` +
    a 5-byte ``status`` string, per exchange segment) while subscribed via
    ``subscribe_exchange()`` / ``unsubscribe_exchange()`` (which send the
    "subscribeExchange" / "unsubscribeExchange" events) -- see
    :class:`MarketStatusCode` for what ``status_code`` means.

    Also delivered from message_code 6511/6521 (header only, in a
    per-instrument feed context, no real body) -- ``status_code`` is
    synthesized as 1/2 to line up with :class:`MarketStatusCode`'s
    BCAST_OPEN_MESSAGE/BCAST_CLOSE_MESSAGE.

    ``status`` is always the static, human-readable text from
    :data:`MARKET_STATUS_TEXT` for the given ``status_code`` (e.g. "Market
    open"), not the raw wire string -- the wire string is unreliable (often
    blank except for status_code 1/2).
    """

    type: Literal["market_status"] = "market_status"
    exchange_segment: str
    status_code: int
    status: str


class SFeedCasChange(SFeedInstrumentMessage):
    """Call auction session (CAS) reference-price/order-imbalance update —
    message_code 104.

    Unlike SFeedMarketStatus, this has a real per-instrument token, so it
    extends SFeedInstrumentMessage (instrument_token + trading_symbol) same
    as SFeedScrip/SFeedScripLite/SFeedIndex. Delivered on subscribe_scrips()/
    subscribe_depth() -- not a separate subscription.
    """

    type: Literal["cas_change"] = "cas_change"
    ref_price: float
    imbalance_qty: int
    imbalance_qty_at_market: int


# Union of all feed message types
SFeedMessage = SFeedScrip | SFeedScripLite | SFeedIndex | SFeedMarketStatus | SFeedCasChange
