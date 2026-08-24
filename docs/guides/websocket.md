# SFeed WebSocket Guide

Modern **async/await** WebSocket client for Kotak Neo's **SFeed** market-data feed
(`native_batch` protocol). Introduced in **v2.2.0**, it replaces the legacy
callback-based WebSocket.

- **URL:** `wss://sfeed.kotaksecurities.com/apifeed`
- **Control plane:** JSON text frames (auth, subscribe, unsubscribe, snapshot)
- **Data plane:** binary frames (little-endian, packed, batched) — decoded for you
  into typed Pydantic messages

> The SDK resolves the actual feed URL for your account automatically (via an
> internal config lookup keyed off the data center from `totp_validate()`),
> which keeps it pointed at whatever endpoint is currently active. This is
> transparent — no configuration is needed; the URL above is simply the
> default used if that lookup doesn't return one.

## Features

- **Async/await API** with `async for` iteration
- **Type-safe** Pydantic messages (`SFeedScrip`, `SFeedScripLite`, `SFeedIndex`, `SFeedCasChange`, `SFeedMarketStatus`)
- **Context manager** for automatic connect/close
- **Batched subscriptions** — any number of instruments in a single frame
- **Retries on initial connect failure** (e.g. a transient network error) before raising
- **Auto-reconnect** with re-authentication and re-subscription after a later drop
- **Automatic price scaling** using the per-exchange dividers from the auth response

## Installation

No extra install step is needed — the SFeed client's dependencies (`websockets`,
`pydantic`) ship with the base package:

```bash
pip install kotakneoapi
```

## Quick Start

```python
import asyncio
from neo_api_client import NeoAPI
from neo_api_client.websocket.feed import WsToken, SFeedScrip


async def main():
    client = NeoAPI(consumer_key="your-consumer-key", environment="prod")
    client.totp_login(mobile_number="+919876543210", ucc="ABC123", totp="123456")
    client.totp_validate(mpin="123456")

    # create_websocket() builds a SFeedWebSocket from the current session
    async with client.create_websocket() as ws:
        await ws.subscribe_scrips([
            WsToken("nse_cm", "Nifty 50"),
            WsToken("nse_cm", "11536"),
        ])

        async for message in ws:
            if isinstance(message, SFeedScrip):
                print(
                    f"{message.trading_symbol} ({message.instrument_token}) "
                    f"LTP: {message.last_traded_price}"
                )


asyncio.run(main())
```

### Constructing the client directly

`create_websocket()` is the convenient path, but you can build the client yourself:

```python
from neo_api_client.websocket.feed import SFeedWebSocket, WsToken

async with SFeedWebSocket() as ws:  # uses SFeed defaults
    await ws.subscribe_scrips([WsToken("nse_cm", "Nifty 50")])
    async for message in ws:
        print(message.model_dump())
```

### Without a context manager

```python
ws = SFeedWebSocket()
await ws.connect()
try:
    await ws.subscribe_scrips([WsToken("nse_cm", "11536")])
    async for message in ws:
        print(message)
finally:
    await ws.close()
```

## Tokens

A `WsToken` pairs an exchange segment with an instrument token. The token may be a
**numeric scrip code** or an **index/instrument name**:

```python
WsToken("nse_cm", "11536")  # numeric token
WsToken("nse_cm", "Nifty 50")  # index by name
WsToken("nse_fo", "44498")  # F&O contract
```

`WsToken` is immutable (hashable), so it can be used in sets and as dict keys.

## Subscription API

Every subscribe/unsubscribe call **batches all tokens into a single frame**.

| Method | Level | Message type received |
|--------|-------|-----------------------|
| `subscribe_scrips(tokens)` | Touch line (4) | `SFeedScrip` |
| `subscribe_scrips_lite(tokens)` | Mini touch line (1) | `SFeedScripLite` |
| `subscribe_depth(tokens)` | Depth (8) | `SFeedScrip` (with `buy`/`sell` rows) |
| `subscribe_full_depth(tokens)` | Full depth (16) | `SFeedScrip` (with `buy`/`sell` rows) |
| `subscribe_index(tokens)` | Index | `SFeedIndex` |
| `subscribe_exchange()` | Market status | `SFeedMarketStatus` |

`subscribe_exchange()`/`unsubscribe_exchange()` take no tokens — they send a single
`{"event": "subscribeExchange"}` / `{"event": "unsubscribeExchange"}` frame, not a
batched one. Like the token-based subscriptions, it's automatically re-sent after a
reconnect.

Each has a matching `unsubscribe_*` method. A one-time snapshot is available via
`snapshot(tokens, intent="scrips")` (intents: `scrips`, `scrips_lite`, `depth`, `index`).
Like `subscribe_scrips()` etc., `snapshot()` also waits for its subscribe
acknowledgement (up to `ack_wait_timeout`) before returning, so a snapshot
call can't leave the live feed's withholding window open behind it (see
[Trading symbol](#trading-symbol)).

### LTP (single instrument)

Subscribe to one instrument — by numeric token or index name — for last-traded-price
updates:

```python
await ws.subscribe_scrips([WsToken("nse_cm", "Nifty 50")])
# ...
await ws.unsubscribe_scrips([WsToken("nse_cm", "Nifty 50")])
```

On the wire this is the documented LTP frame
`{"event": "subscribeScrips", "inputtoken": "nse_cm|Nifty 50", "ack_symbol": true}`
(`ack_symbol` requests the trading-symbol acknowledgement; see
[Trading symbol](#trading-symbol)).

### Option chain (batched)

Pass the whole chain in one call — all tokens are sent in a single frame as a
comma-separated `inputtoken` (e.g. `nse_fo|44498,nse_fo|44500,...`):

```python
chain = [WsToken("nse_fo", str(t)) for t in range(44498, 44520)]
await ws.subscribe_scrips(chain)  # one batched frame
# ...
await ws.unsubscribe_scrips(chain)  # one batched frame
```

### Subscription limit

A client may hold at most **3000 input tokens** subscribed at once. This cap is a
**running total across every subscribe request** — LTP, option chain, index, depth,
etc. all draw from the same budget.

- A request whose new tokens would push the total over the limit raises
  `SubscriptionError` and **nothing is sent** (the existing subscriptions are left
  untouched).
- Tokens already subscribed do not count again, so re-subscribing is safe.
- `unsubscribe_*` frees budget; `ws.subscription_count` reports the current usage.
- The limit is configurable via `max_subscriptions` (see
  [Configuration](#configuration)).

```python
await ws.subscribe_scrips(ltp_tokens)  # e.g. 500 tokens
await ws.subscribe_scrips(option_chain)  # e.g. 2400 tokens -> total 2900, OK
await ws.subscribe_scrips(more_tokens)  # would exceed 3000 -> SubscriptionError

print(ws.subscription_count)  # tokens currently subscribed
```

## Message Types

All prices are already scaled (divided by the per-exchange divider) before you receive them.

Every message carries `exchange_segment`. Instrument-specific messages
(`SFeedScrip`, `SFeedScripLite`, `SFeedIndex`, `SFeedCasChange`) also carry
`instrument_token` and `trading_symbol` (see [Trading symbol](#trading-symbol)
below). `SFeedMarketStatus` is the one exception — it isn't tied to a
specific instrument, so it has neither field (see below).

### `SFeedScrip` — touch line / depth / full depth

```python
from neo_api_client.websocket.feed import SFeedScrip

async for message in ws:
    if isinstance(message, SFeedScrip):
        print(f"LTP: {message.last_traded_price}")
        print(f"Change: {message.net_change} ({message.net_change_percent}%)")
        print(f"Volume: {message.volume_traded_today}")
        print(
            f"OHLC: {message.open_price}/{message.high_price}/"
            f"{message.low_price}/{message.close_price}"
        )
        for row in message.buy:  # depth rows (empty for touch line)
            print(f"  bid {row.price} x {row.quantity} ({row.orders} orders)")
```

Key fields: `last_traded_price`, `open_price`, `high_price`, `low_price`,
`close_price`, `average_trade_price`, `net_change`, `net_change_percent`,
`total_buy_quantity`, `total_sell_quantity`, `volume_traded_today`, `open_interest`,
`upper_circuit_limit`, `lower_circuit_limit`, `yearly_high`, `yearly_low`,
`total_traded_value`, `market_lot`, `precision`, `last_trade_time`,
`last_update_time`, `buy` / `sell` (lists of `DepthLevel`).

`last_update_time` is `0` for an instrument that has never been updated,
same convention as `last_trade_time` — the exchange actually sends a
negative sentinel (`1900-01-01 00:00:00 IST` as a signed Unix timestamp,
e.g. `-2209008600`) for this case, but the SDK normalizes it to `0` before
delivering the message.

### `SFeedScripLite` — mini touch line (bandwidth-optimized)

```python
await ws.subscribe_scrips_lite([WsToken("nse_cm", "11536")])

async for message in ws:
    if isinstance(message, SFeedScripLite):
        print(f"LTP: {message.last_traded_price}, chg%: {message.net_change_percent}")
```

Fields: `last_traded_price`, `last_trade_time`, `last_trade_qty`, `close_price`,
`net_change`, `net_change_percent`, `market_lot`, `precision`, `multiplier`.

### `SFeedIndex`

```python
await ws.subscribe_index([WsToken("nse_cm", "Nifty 50")])

async for message in ws:
    if isinstance(message, SFeedIndex):
        print(f"{message.name}: {message.last_traded_price} (chg {message.change})")
```

### `SFeedCasChange`

Call auction session (CAS) reference-price/order-imbalance update
(message code 104). Delivered on `subscribe_scrips()`/`subscribe_depth()`
alongside normal touch-line/depth data — not a separate subscription:

```python
from neo_api_client.websocket.feed import SFeedCasChange

await ws.subscribe_scrips([WsToken("nse_cm", "1333")])

async for message in ws:
    if isinstance(message, SFeedCasChange):
        print(
            f"{message.trading_symbol} ({message.instrument_token}) "
            f"ref_price={message.ref_price} imbalance_qty={message.imbalance_qty} "
            f"imbalance_qty_at_market={message.imbalance_qty_at_market}"
        )
```

Fields: `ref_price` (scaled by the per-exchange divider, like every other
price field), `imbalance_qty`, `imbalance_qty_at_market`.

Only meaningful during the CAS window — outside it, the exchange still
broadcasts this packet but with `ref_price`, `imbalance_qty`, and
`imbalance_qty_at_market` all zero. The SDK drops that case entirely (you
never see it via `async for`/`on_message`) rather than delivering a message
with nothing useful in it. A message with only *some* of those three at
zero is still delivered — it's only dropped when all three are zero.

### `SFeedMarketStatus`

Received both from touch-line-style subscriptions (message codes 6511/6521 —
header only, no body) and from [`subscribe_exchange()`](#subscription-api)
(message code 105, which carries a real body: `status_code` + a `status`
string) — both decode to this same type:

```python
from neo_api_client.websocket.feed import MarketStatusCode

await ws.subscribe_exchange()

async for message in ws:
    if isinstance(message, SFeedMarketStatus):
        print(f"status_code={message.status_code} status={message.status}")
        if message.status_code == MarketStatusCode.BCAST_CLOSING_START:
            ...
```

Fields: `exchange_segment`, `status_code`, `status`. Unlike every other
message type, there's no `instrument_token` or `trading_symbol` here — the
wire packet carries no token field at all, so the model only exposes what
the feed actually sends.

`status_code` (from `subscribe_exchange()`'s message code 105; synthesized as
`1`/`2` for the header-only 6511/6521 case) is one of:

| Code | `MarketStatusCode` member | `status` text |
|------|---------------------------|----------------|
| 1 | `BCAST_OPEN_MESSAGE` | Market open |
| 2 | `BCAST_CLOSE_MESSAGE` | Market closed |
| 3 | `BCAST_PREOPEN_SHUTDOWN_MSG` | Pre-open session ending |
| 4 | `BCAST_NORMAL_MKT_PREOPEN_ENDED` | Pre-open ended, normal market open |
| 5 | `BCAST_AUCTION_STATUS_CHANGE` | Auction status changed |
| 6 | `BCAST_CLOSING_START` | Closing session started |
| 7 | `BCAST_CLOSING_END` | Closing session ended |
| 8 | `BCAST_CTS_CLOSE_FOR_CAS` | Continuous trading closed, closing auction starting soon |
| 9 | `BCAST_REVISED_PRICE_BAND_COMPLETED` | Closing auction price band set |
| 10 | `BCAST_CAS_START` | Closing auction (CAS) started |
| 11 | `BCAST_MARKET_ORDER_RESTRICTED` | Market orders restricted |
| 12 | `BCAST_CAS_END` | Closing auction (CAS) ended |

`status` is this static, human-readable text (from `MARKET_STATUS_TEXT`,
keyed by `status_code`) — **not** the raw wire string. The wire string is
unreliable in practice (the live feed sends an empty string for most codes
other than 1); a `status_code` not yet in the table above falls back to the
wire string, then to a placeholder, in that order.

`subscribe_exchange()`/`unsubscribe_exchange()` take **no arguments at all** —
not tokens, not an `inputtoken`, nothing. Calling either with any positional
or keyword argument raises `TypeError` (enforced by the method signature
itself, not just documented convention).

### Handling multiple types

```python
from neo_api_client.websocket.feed import SFeedScrip, SFeedIndex

async for message in ws:
    match message:
        case SFeedScrip():
            print(f"Scrip {message.instrument_token}: {message.last_traded_price}")
        case SFeedIndex():
            print(f"Index {message.name}: {message.last_traded_price}")
```

## Trading symbol

The binary feed does not include the human-readable trading symbol — the server
sends it once, in the **subscribe acknowledgement** (control frame with
`message_code` 1109). The client requests this by sending `ack_symbol: true` on
every subscribe frame automatically, captures the returned mapping, and stamps
every subsequent message with its `trading_symbol`:

```python
await ws.subscribe_scrips([WsToken("nse_cm", "2885")])

async for message in ws:
    # trading_symbol is resolved from the subscribe ack, e.g. "RELIANCE-EQ"
    print(f"{message.trading_symbol} ({message.instrument_token}): {message.last_traded_price}")
```

Details:

- While a subscribe acknowledgement is outstanding, only messages for
  instruments whose `trading_symbol` is still unknown are withheld —
  instruments already resolved by an earlier subscribe keep streaming
  immediately, unaffected by a later, unrelated subscribe call. Withheld
  messages are decoded but not delivered; instead of queuing every one
  (which would deliver a backlog of stale ticks once the ack lands), the
  client keeps only the **latest message per `(instrument, message
  type/level)`** in an in-memory map — each new message for the same key
  overwrites the previous one. In-between ticks during the wait are
  discarded on purpose: the latest tick per key is preserved, not every
  tick, matching a live feed where an out-of-date price is superseded the
  moment a newer one arrives. Market-open/close events are never withheld
  (they'd otherwise collide on one shared key and a later "closed" could
  erase an earlier "open"). As soon as the ack arrives, every held-back
  key's latest message is delivered in one go, enriched with its now-known
  `trading_symbol` — never a message with `trading_symbol=None` from a
  mapping that was about to arrive anyway. The window is bounded by
  `ack_wait_timeout` (default 5.0s, set via `SFeedWebSocket(...,
  ack_wait_timeout=...)`) **per subscribe call** — two overlapping
  subscribes each get their own timeout, so one arriving early doesn't
  release the other's still-unresolved instruments early. If the timeout
  elapses without an ack, the same release happens anyway (with
  `trading_symbol=None` for instruments the map has no entry for), and
  normal per-message delivery resumes. Use `ws.pending_message_count` to
  see how many keys are currently withheld.
- `subscribe_scrips()` (and the other `subscribe_*` methods) wait for the
  acknowledgement before returning (up to `ack_wait_timeout`), so
  `ws.trading_symbols` is already populated by the time the call completes.
- `trading_symbol` is `None` for any token the server didn't return a
  symbol for, or if no ack arrived before `ack_wait_timeout` elapsed.
- The mapping is keyed by `"<exchange_segment>|<instrument_token>"` — i.e. by
  whatever `instrument_token` you subscribed with (see `WsToken`). You can
  inspect the current map via the read-only `ws.trading_symbols` property.
- **Indices are the one exception.** They're subscribed by name (e.g.
  `WsToken("nse_cm", "Nifty 50")`), so the ack maps that name to the trading
  symbol — but the streamed `SFeedIndex` message itself carries the numeric
  `instrument_token` the server resolved the index to, not the name. The
  client accounts for this automatically (falling back to a name-keyed
  lookup for index messages), so `trading_symbol` still resolves correctly;
  this is only worth knowing if you're inspecting `ws.trading_symbols`
  directly and wondering why an index's entry is keyed by name rather than
  by the `instrument_token` on the messages you receive for it.
- On **unsubscribe**, a token's entry is removed once it is no longer subscribed
  under any feed level (so unsubscribing touch line while depth is still active
  keeps the symbol).
- On reconnect, the client re-subscribes and the server re-sends the
  acknowledgements, so the map is rebuilt automatically.

## Configuration

`SFeedWebSocket(...)` / `client.create_websocket(**kwargs)` accept:

| Argument | Default | Purpose |
|----------|---------|---------|
| `url` | `wss://sfeed.kotaksecurities.com/apifeed` | Feed endpoint (auto-resolved per account; see note above — pass explicitly to override) |
| `user` / `auth` | `ucc` / `sid` | SFeed credentials — `user` is your UCC, `auth` is your `sid` (both from the `totp_validate()` response), auto-filled from your session; no need to set these yourself |
| `source` / `platform` / `version` / `sdk_version` / `sdk_date` | `"NEOTRADEAPI"` / internal defaults | Client/build identification sent to the feed. `source` is always `"NEOTRADEAPI"` — no need to change these |
| `session_validation` | `False` | `sessionValidation` auth field |
| `reconnect_delay` | `5` | Seconds between reconnect attempts (also used between initial connect retries) |
| `max_reconnect_attempts` | `5` | Cap on reconnect attempts after a previously established connection later drops |
| `max_connect_retries` | `3` | Cap on retries for the *initial* `connect()` call itself if opening the socket fails (e.g. a transient network error). Set to `0` to fail immediately with no retries |
| `ping_interval` | `20` | WebSocket keep-alive ping interval (seconds) |
| `max_subscriptions` | `3000` | Max total input tokens subscribed at once (across all requests) |
| `ack_wait_timeout` | `5.0` | Seconds `subscribe_scrips()` (etc.) wait for the subscribe acknowledgement — see [Trading symbol](#trading-symbol) |

## Event Callbacks (optional)

Alongside `async for`, you can attach callbacks:

```python
ws.on_message = lambda msg: print(msg)  # each decoded message
ws.on_error = lambda err: print(f"error: {err}")
ws.on_connect = lambda: print("connected")
ws.on_disconnect = lambda: print("disconnected")
ws.on_raw = lambda frame: print(repr(frame))  # raw wire frame (debugging)
```

## Error Handling

```python
from neo_api_client.websocket.feed.exceptions import (
    ConnectionError,
    AuthenticationError,
    SubscriptionError,
    NotConnectedError,
)

try:
    async with client.create_websocket() as ws:
        await ws.subscribe_scrips([WsToken("nse_cm", "Nifty 50")])
        async for message in ws:
            ...
except AuthenticationError as e:
    print(f"Auth failed: {e}")
except ConnectionError as e:
    print(f"Connection failed: {e}")
except SubscriptionError as e:
    print(f"Subscription failed: {e}")
```

A single malformed data frame never tears down the receive loop — decode issues are
reported through `on_error` and the stream continues.

## Migration from the Legacy WebSocket (removed in v2.2.0)

The old callback WebSocket (`client.subscribe(...)`, `client.un_subscribe(...)`,
`client.subscribe_to_orderfeed()`, and the `on_message`/`on_error`/`on_open`/`on_close`
attributes) has been **removed**. Those methods now raise `NotImplementedError`
pointing here.

**Before (removed):**
```python
def on_message(message):
    ltp = message["data"]["ltp"]


client.on_message = on_message
client.subscribe(instrument_tokens=[{"instrument_token": "11536", "exchange_segment": "nse_cm"}])
```

**After (SFeed):**
```python
async with client.create_websocket() as ws:
    await ws.subscribe_scrips([WsToken("nse_cm", "11536")])
    async for message in ws:
        ltp = message.last_traded_price
```

| Legacy | SFeed |
|--------|---------|
| `client.subscribe(instrument_tokens=[{...}])` | `await ws.subscribe_scrips([WsToken(...)])` |
| `client.un_subscribe(...)` | `await ws.unsubscribe_scrips([...])` |
| `isIndex=True` | `await ws.subscribe_index([...])` |
| `isDepth=True` | `await ws.subscribe_depth([...])` / `subscribe_full_depth` |
| `client.on_message = cb` (dict payload) | `async for message in ws:` (typed model) |
| `message["ltp"]` | `message.last_traded_price` |

## Testing

Run the WebSocket-related unit tests (no live connection required — they use a fake
socket and synthetic binary packets):

```bash
pytest tests/unit/test_feed_client.py tests/unit/test_feed_protocol.py -v
```

An end-to-end example lives at [`examples/feed_websocket_example.py`](../../examples/feed_websocket_example.py).
The smoke test ([`tests/e2e/smoke_test.py`](../../tests/e2e/smoke_test.py)) exercises live
subscribe/receive/unsubscribe cycles for these flows:

- **WEBSOCKET LTP SUBSCRIBE** / **WEBSOCKET LTP UNSUBSCRIBE** — a single index token
  (`nse_cm|Nifty 50`)
- **WEBSOCKET OPTION CHAIN SUBSCRIBE** / **WEBSOCKET OPTION CHAIN UNSUBSCRIBE** — a batch
  of `nse_fo` option tokens sent in one frame
- **WEBSOCKET MARKET SUBSCRIBE** / **WEBSOCKET MARKET UNSUBSCRIBE** — `subscribe_exchange()`
  / `unsubscribe_exchange()` (no tokens), receiving `SFeedMarketStatus`

The unsubscribe cases also confirm the feed goes quiet after unsubscribing.

### Logging

Both `SFeedWebSocket` and `OrderFeedWebSocket` log connect/reconnect/
disconnect/authentication/subscription events through the SDK's shared
logger. See the [Logging Guide](logging.md) for the full set of log levels,
`setup_logging(...)` usage, and configuration.
