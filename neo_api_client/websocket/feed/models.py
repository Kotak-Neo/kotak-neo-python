"""Pydantic models for SFeed WebSocket feed messages (native_batch).

Field values here are already decoded and scaled (prices divided by the
per-exchange divider, net_chg_percent divided by 100) by
:mod:`neo_api_client.websocket.feed.protocol`.
"""

from enum import IntEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


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
    # Resolved from the subscribe acknowledgement (message_code 1109) and
    # attached by the client. None until the mapping is known for this token.
    trading_symbol: str | None = None


class DepthLevel(BaseModel):
    """A single market-depth row (bid or ask)."""

    quantity: int
    price: float
    orders: int


class SFeedScrip(SFeedBase):
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


class SFeedScripLite(SFeedBase):
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


class SFeedIndex(SFeedBase):
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


class SFeedMarketStatus(SFeedBase):
    """Market open/close notification — message_code 6511 / 6521 (header only)."""

    type: Literal["market_status"] = "market_status"
    status: Literal["open", "close"]


# Union of all feed message types
SFeedMessage = SFeedScrip | SFeedScripLite | SFeedIndex | SFeedMarketStatus
