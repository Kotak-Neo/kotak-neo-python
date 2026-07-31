# WebSocket — Order & Position Feed

Stream real-time **order-lifecycle events** (new, validation, open, complete,
rejected, cancelled, ...) and live **position updates** over a dedicated
async/await WebSocket, `OrderFeedWebSocket` (introduced in v2.2.0).

This is separate from the market-data **[SFeed](../../guides/websocket.md)**
feed (`create_websocket()`): market data flows over `SFeedWebSocket`, while order
and position updates flow over `OrderFeedWebSocket` (`create_order_feed()`).

> The legacy callback-based `client.subscribe_to_orderfeed()` was **removed in
> v2.2.0** and now raises `NotImplementedError`.

## Endpoint & authentication

The feed lives at `wss://<baseurl>/realtime`, where `<baseurl>` is the host
returned by `totp_validate()` (stored on the configuration as `base_url`). You
must complete `totp_login()` **and** `totp_validate()` before creating the feed.

Immediately after the socket opens the client sends a single **raw (non-JSON)**
handshake string — this is handled for you:

```text
{type:cn,Authorization:<edit_token>,Sid:<edit_sid>,src:WEB}
```

The server replies with a connection acknowledgement (`{"ak":"ok","type":"cn",...}`),
which the client consumes internally — it is not surfaced as a message.

## Quick start

Create the client from an authenticated session with `create_order_feed()`, then
iterate with `async for`:

```python
import asyncio
from neo_api_client import NeoAPI
from neo_api_client.websocket.orderfeed import OrderUpdate, PositionUpdate, OrderStatus


async def main():
    client = NeoAPI(consumer_key="your-consumer-key", environment="prod")
    client.totp_login(mobile_number="+919876543210", ucc="YOUR_UCC", totp="123456")
    client.totp_validate(mpin="123456")

    async with client.create_order_feed() as feed:
        async for message in feed:
            if isinstance(message, OrderUpdate):
                print(f"order {message.data.order_id} -> {message.data.order_status}")
                if message.data.order_status == OrderStatus.COMPLETE:
                    print("order fully executed")
            elif isinstance(message, PositionUpdate):
                print(
                    f"position {message.data.symbol}: "
                    f"buy={message.data.filled_buy_quantity} "
                    f"sell={message.data.filled_sell_quantity}"
                )


asyncio.run(main())
```

### Callback style

If you prefer callbacks over `async for`, assign the hooks before connecting:

```python
feed = client.create_order_feed()
feed.on_connect = lambda: print("connected")
feed.on_message = lambda m: print("message:", m)
feed.on_error = lambda e: print("error:", e)
feed.on_disconnect = lambda: print("disconnected")
feed.on_raw = lambda frame: print("raw frame:", frame)  # every frame, pre-parse

await feed.connect()
# ... keep the loop alive ...
await feed.close()
```

## Message types

Frames are decoded into typed Pydantic models based on the top-level `type`
discriminator. Every field is optional and unknown fields are preserved
(`extra="allow"`), so partial or evolving payloads never fail to parse.

| `type`              | Model            | Meaning                                                                 |
|---------------------|------------------|--------------------------------------------------------------------------|
| `order`             | `OrderUpdate`    | Order-lifecycle state change                                            |
| `position`          | `PositionUpdate` | Live position update                                                    |
| `cn`                | *(dropped)*      | Connection ack (control frame)                                          |
| anything else       | raw `dict`       | Unrecognized `type` — surfaced as-is                                    |
| unparseable payload | raw `dict`/`str` | Payload didn't fit `OrderUpdate`/`PositionUpdate`, or wasn't valid JSON  |

**Not every message is a typed model.** If `type` isn't `"order"` or
`"position"`, or a payload with one of those types doesn't fit the
corresponding Pydantic model, `_parse_message()` falls back to returning the
raw `dict` (or, if the frame wasn't valid JSON, the raw `str`) instead of
raising. This is intentional — a single malformed or unexpected frame must
never tear down the receive loop. In the "doesn't fit the model" case,
`on_error` (if set) is invoked with the parse exception, but the raw payload
is still delivered through `async for` / `on_message`.

Practical implication: **don't call `message.model_dump()` (or access
`message.data`) unconditionally** — check the type first:

```python
async for message in feed:
    if isinstance(message, (OrderUpdate, PositionUpdate)):
        print(message.model_dump())
    else:
        # Unrecognized type, or a payload that didn't fit the model:
        # a plain dict (occasionally a raw string).
        print("unhandled frame:", message)
```

### Order lifecycle (observed)

An order typically moves through these `order_status` (`ordSt`) values:

1. `put order req received`
2. `validation pending`
3. `open pending`
4. `open`
5. `complete`

Other terminal/transition states: `rejected`, `cancelled`, `modified`. Use the
`OrderStatus` constants for readable comparisons — but treat them as a reference
list, not a closed enum: `order_status` is a plain string and the server may emit
new values, which are surfaced as-is.

### `OrderUpdate.data` (`OrderData`) fields

| Attribute                    | Wire alias | Notes                          |
|------------------------------|------------|--------------------------------|
| `order_id`                   | `nOrdNo`   | Internal order number/ID — same identifier as `order_id` in `order_report()`/`order_history()`/`modify_order()`/`cancel_order()` |
| `exchange_order_id`          | `exOrdId`  | Exchange order ID              |
| `order_status`               | `ordSt`    | Order status (see above)       |
| `average_price`              | `avgPrc`   | Average traded price           |
| `quantity`                   | `qty`      | Total order quantity           |
| `filled_quantity`            | `fldQty`   | Filled quantity                |
| `unfilled_size`              | `unFldSz`  | Remaining quantity             |
| `transaction_type`           | `trnsTp`   | `B` = Buy, `S` = Sell          |
| `price_type`                 | `prcTp`    | `MKT`, `LMT`, ...              |
| `product`                    | `prod`     | `NRML`, `MIS`, ...             |
| `exchange_segment`           | `exSeg`    | Exchange segment               |
| `symbol`                     | `sym`      | Trading symbol                 |
| `trading_symbol`             | `trdSym`   | Trading symbol with series     |
| `token`                      | `tok`      | Exchange token                 |
| `order_date_time`            | `ordDtTm`  | Order date/time                |
| `update_receive_time`        | `updRecvTm`| Update receive timestamp (ns)  |
| `exchange_broadcast_time`    | `boeSec`   | Broadcast time (epoch seconds) |
| `exchange_confirmation_time` | `exCfmTm`  | Exchange confirmation time     |

### `PositionUpdate.data` (`PositionData`) fields

All financial fields are strings on the wire.

| Attribute               | Wire alias   | Notes                    |
|-------------------------|--------------|--------------------------|
| `account_id`            | `actId`      | Account ID               |
| `symbol`                | `sym`        | Symbol                   |
| `exchange_segment`      | `exSeg`      | Exchange segment         |
| `product`               | `prod`       | Product type             |
| `filled_buy_quantity`   | `flBuyQty`   | Filled buy quantity      |
| `filled_sell_quantity`  | `flSellQty`  | Filled sell quantity     |
| `buy_amount`            | `buyAmt`     | Total buy amount         |
| `sell_amount`           | `sellAmt`    | Total sell amount        |
| `position_flag`         | `posFlg`     | Position active flag     |
| `square_off_flag`       | `sqrFlg`     | Square-off allowed flag  |
| `lot_size`              | `lotSz`      | Lot size                 |
| `multiplier`            | `multiplier` | Contract multiplier      |
| `update_time`           | `hsUpTm`     | Update timestamp         |

## `create_order_feed(**kwargs)`

Builds an `OrderFeedWebSocket` from the current session (`base_url`, `edit_token`,
`edit_sid`). Extra keyword arguments are forwarded to the client:

| Keyword                  | Default | Description                                   |
|--------------------------|---------|-----------------------------------------------|
| `source`                 | `"WEB"` | `src` value in the connection payload         |
| `reconnect_delay`        | `5`     | Seconds between reconnect attempts (also used between initial connect retries) |
| `max_reconnect_attempts` | `5`     | Cap on reconnect attempts after a previously established connection later drops |
| `max_connect_retries`    | `3`     | Cap on retries for the *initial* `connect()` call itself if opening the socket fails. Set to `0` to fail immediately with no retries |
| `ping_interval`          | `20`    | WebSocket-level keep-alive ping interval (s)  |

**Raises `ValueError`** if not authenticated (missing `edit_token`/`edit_sid`) or
the base URL is unavailable (`totp_validate()` not completed).

## Reconnection & production handling

- If the **initial** `connect()` call fails to open the socket (e.g. a transient
  network error), it's retried up to `max_connect_retries` times, waiting
  `reconnect_delay` seconds between attempts, before raising `ConnectionError`.
  This does not cover sending the connection payload afterward — an
  `AuthenticationError` there usually isn't transient, so it's raised immediately.
- On an unexpected disconnect **after** a connection has already succeeded once,
  the client automatically reconnects, up to `max_reconnect_attempts`, waiting
  `reconnect_delay` seconds between attempts. This is a separate cap from
  `max_connect_retries`.
- On reconnect the server pushes current state again, so no manual resubscription
  is needed.
- The feed is **fire-and-hose**: it streams whatever the account produces; there
  is no subscribe/unsubscribe step (unlike the market-data SFeed feed).
- Set `on_error` to observe transport/parse errors; a single malformed frame is
  logged via `on_error` and never tears down the receive loop.
- Always `close()` the feed (or use `async with`) to cancel the receive task and
  close the socket cleanly.

## Related

- **[Market Feed (Subscribe/Unsubscribe)](./market_feed.md)** — market-data SFeed feed
- **[SFeed WebSocket Guide](../../guides/websocket.md)** — market-data client reference

[[Back to top]](#) [[Back to functions]](../README.md) [[Back to README]](../../../README.md)
