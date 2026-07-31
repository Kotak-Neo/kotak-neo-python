"""Pydantic models for Order & Position streaming messages.

The feed sends JSON frames with a top-level ``type`` discriminator:

* ``order``    -> :class:`OrderUpdate`  (order-lifecycle state change)
* ``position`` -> :class:`PositionUpdate` (live position update)

The connection acknowledgement (``type: "cn"``) is a control frame and is not
modeled here — the client consumes it during the handshake.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class OrderStatus:
    """Known order-lifecycle status values for the ``ordSt`` field.

    These are the states observed on the stream — use them for readable
    comparisons, e.g. ``if update.data.order_status == OrderStatus.COMPLETE``.

    Note: this is a reference list, not an exhaustive/closed enum. The server
    may emit other values; ``OrderData.order_status`` is a plain string and is
    never validated against this list, so new states are surfaced as-is.
    """

    PUT_ORDER_REQ_RECEIVED = "put order req received"
    VALIDATION_PENDING = "validation pending"
    OPEN_PENDING = "open pending"
    OPEN = "open"
    COMPLETE = "complete"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    MODIFIED = "modified"


class OrderData(BaseModel):
    """Order payload (the ``data`` object of an ``order`` message).

    Fields use the wire abbreviations as aliases; unknown fields are preserved
    (``extra="allow"``) and every field is optional so partial/evolving payloads
    never fail to parse.
    """

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    order_id: str | None = Field(None, alias="nOrdNo")  # internal order number/ID
    exchange_order_id: str | None = Field(None, alias="exOrdId")  # exchange order ID
    order_status: str | None = Field(None, alias="ordSt")  # order status
    average_price: str | None = Field(None, alias="avgPrc")  # average traded price
    quantity: int | None = Field(None, alias="qty")  # total order quantity
    filled_quantity: int | None = Field(None, alias="fldQty")  # filled quantity
    unfilled_size: int | None = Field(None, alias="unFldSz")  # remaining quantity
    transaction_type: str | None = Field(None, alias="trnsTp")  # B = Buy, S = Sell
    price_type: str | None = Field(None, alias="prcTp")  # MKT, LMT, etc.
    product: str | None = Field(None, alias="prod")  # NRML, MIS, etc.
    exchange_segment: str | None = Field(None, alias="exSeg")  # exchange segment
    symbol: str | None = Field(None, alias="sym")  # trading symbol
    trading_symbol: str | None = Field(None, alias="trdSym")  # trading symbol with series
    token: str | None = Field(None, alias="tok")  # exchange token
    order_date_time: str | None = Field(None, alias="ordDtTm")  # order date/time
    update_receive_time: int | None = Field(None, alias="updRecvTm")  # update recv ts (ns)
    exchange_broadcast_time: int | None = Field(None, alias="boeSec")  # broadcast time (epoch s)
    exchange_confirmation_time: str | None = Field(None, alias="exCfmTm")  # exchange confirm time


class OrderUpdate(BaseModel):
    """An ``order`` streaming message (state change in the order lifecycle)."""

    type: Literal["order"] = "order"
    data: OrderData


class PositionData(BaseModel):
    """Position payload (the ``data`` object of a ``position`` message).

    All numeric financial fields are strings on the wire (per the spec). Every
    field is optional and unknown fields are preserved (``extra="allow"``) so
    partial/evolving payloads never fail to parse.
    """

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    account_id: str | None = Field(None, alias="actId")  # account ID
    symbol: str | None = Field(None, alias="sym")  # symbol
    exchange_segment: str | None = Field(None, alias="exSeg")  # exchange segment
    product: str | None = Field(None, alias="prod")  # product type
    filled_buy_quantity: str | None = Field(None, alias="flBuyQty")  # filled buy qty
    filled_sell_quantity: str | None = Field(None, alias="flSellQty")  # filled sell qty
    buy_amount: str | None = Field(None, alias="buyAmt")  # total buy amount
    sell_amount: str | None = Field(None, alias="sellAmt")  # total sell amount
    position_flag: str | None = Field(None, alias="posFlg")  # position active flag
    square_off_flag: str | None = Field(None, alias="sqrFlg")  # square-off allowed flag
    lot_size: str | None = Field(None, alias="lotSz")  # lot size
    multiplier: str | None = Field(None, alias="multiplier")  # contract multiplier
    update_time: str | None = Field(None, alias="hsUpTm")  # update timestamp


class PositionUpdate(BaseModel):
    """A ``position`` streaming message (live position update)."""

    type: Literal["position"] = "position"
    data: PositionData


# Union of modeled streaming message types.
OrderFeedMessage = OrderUpdate | PositionUpdate


# Union of modeled streaming message types.
OrderFeedMessage = OrderUpdate | PositionUpdate
