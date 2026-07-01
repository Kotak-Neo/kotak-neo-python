"""Pydantic models for Srishti WebSocket messages."""

from typing import Literal

from pydantic import BaseModel, Field


class WsToken(BaseModel):
    """WebSocket token for subscription.

    Args:
        exchange_segment: Exchange segment (e.g., 'nse_cm', 'bse_cm', 'nse_fo', 'mcx_fo')
        instrument_token: Instrument token/scrip code

    Example:
        ```python
        token = WsToken("nse_cm", "1333")  # RELIANCE
        token = WsToken("mcx_fo", "499095")
        ```
    """

    exchange_segment: str = Field(..., description="Exchange segment")
    instrument_token: str = Field(..., description="Instrument token")

    def __init__(self, exchange_segment: str, instrument_token: str):
        """Create a WsToken.

        Args:
            exchange_segment: Exchange segment
            instrument_token: Instrument token
        """
        super().__init__(exchange_segment=exchange_segment, instrument_token=instrument_token)

    class Config:
        frozen = True  # Make immutable for use as dict keys


class SFeedBase(BaseModel):
    """Base model for all Srishti feed messages."""

    exchange_segment: str = Field(..., alias="exchangeSegment")
    instrument_token: str = Field(..., alias="token")

    class Config:
        populate_by_name = True  # Allow both alias and field name


class SFeedScrip(SFeedBase):
    """Full scrip data feed.

    Contains complete market data including OHLC, volume, depth summary, and circuit limits.
    """

    type: Literal["scrip"] = "scrip"
    is_mini: bool = Field(False, alias="isMini")
    last_traded_price: float = Field(..., alias="lastTradedPrice")
    percentage_change: float = Field(..., alias="percentageChange")
    change: float
    open_price: float = Field(..., alias="openPrice")
    high_price: float = Field(..., alias="highPrice")
    low_price: float = Field(..., alias="lowPrice")
    close_price: float = Field(..., alias="closePrice")
    vwap_average_price: float = Field(..., alias="vwapAveragePrice")
    last_trade_quantity: int = Field(..., alias="lastTradeQuantity")
    trade_volume: int = Field(..., alias="tradeVolume")
    total_buy_quantity: int = Field(..., alias="totalBuyQuantity")
    total_sell_quantity: int = Field(..., alias="totalSellQuantity")
    open_interest: int = Field(..., alias="openInterest")
    last_trade_time: int = Field(..., alias="lastTradeTime")
    multiplier: int
    precision: int
    upper_circuit_limit: float = Field(..., alias="upperCircuitLimit")
    lower_circuit_limit: float = Field(..., alias="lowerCircuitLimit")
    best_offer_price: float = Field(..., alias="bestOfferPrice")
    best_bid_price: float = Field(..., alias="bestBidPrice")
    best_bid_size: int = Field(..., alias="bestBidSize")
    fifty_two_week_high: float = Field(..., alias="fiftyTwoWeekHighOrYearlyHigh")
    fifty_two_week_low: float = Field(..., alias="fiftyTwoWeekHighOrYearlyLow")
    turnover: float


class SFeedScripLite(SFeedBase):
    """Lite scrip data feed.

    Contains only essential market data - LTP, change, and timestamp.
    Use for bandwidth optimization when full data is not needed.
    """

    type: Literal["scrip_lite"] = "scrip_lite"
    last_traded_price: float = Field(..., alias="lastTradedPrice")
    percentage_change: float = Field(..., alias="percentageChange")
    change: float
    last_trade_time: int = Field(..., alias="lastTradeTime")
    multiplier: int
    precision: int


class SFeedIndex(SFeedBase):
    """Index data feed.

    Contains index values and OHLC data.
    """

    type: Literal["index"] = "index"
    last_traded_price: float = Field(..., alias="lastTradedPrice")
    change: float
    percentage_change: float = Field(..., alias="percentageChange")
    open_price: float = Field(..., alias="openPrice")
    high_price: float = Field(..., alias="highPrice")
    low_price: float = Field(..., alias="lowPrice")
    close_price: float = Field(..., alias="closePrice")
    last_trade_time: int = Field(..., alias="lastTradeTime")
    multiplier: int
    precision: int


class SFeedDepth(SFeedBase):
    """Market depth data feed.

    Contains aggregated buy/sell quantities and last update time.
    """

    type: Literal["depth"] = "depth"
    total_buy_qty: int = Field(..., alias="totalBuyQty")
    total_sell_qty: int = Field(..., alias="totalSellQty")
    last_update_time: int = Field(..., alias="lastUpdateTime")


# Union type for all feed messages
SFeedMessage = SFeedScrip | SFeedScripLite | SFeedIndex | SFeedDepth
