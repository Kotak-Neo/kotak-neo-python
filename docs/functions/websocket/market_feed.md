# WebSocket — Market Feed: Subscribe / Unsubscribe (SFeed)

Live market data is delivered through the modern async/await **SFeed** WebSocket
client (introduced in v2.2.0). The legacy callback-based `client.subscribe(...)` /
`client.un_subscribe(...)` API was **removed in v2.2.0** and now raises
`NotImplementedError`.

> Full reference: **[SFeed WebSocket Guide](../../guides/websocket.md)**

## Subscribe

Create the client from an authenticated session with `create_websocket()`, then use the
typed subscribe methods. Every call batches all tokens into a single frame.

```python
import asyncio
from neo_api_client import NeoAPI
from neo_api_client.websocket.feed import WsToken, SFeedScrip


async def main():
    client = NeoAPI(consumer_key="your-consumer-key", environment="prod")
    client.totp_login(mobile_number="+919876543210", ucc="YOUR_UCC", totp="123456")
    client.totp_validate(mpin="123456")

    async with client.create_websocket() as ws:
        await ws.subscribe_scrips([
            WsToken("nse_cm", "11536"),
            WsToken("nse_cm", "Nifty 50"),  # index/instrument by name is allowed
        ])

        async for message in ws:
            if isinstance(message, SFeedScrip):
                print(
                    f"{message.trading_symbol} ({message.instrument_token}) "
                    f"LTP: {message.last_traded_price}"
                )


asyncio.run(main())
```

### Subscription methods

| Method | Data level | Message type |
|--------|-----------|--------------|
| `subscribe_scrips(tokens)` | Touch line | `SFeedScrip` |
| `subscribe_scrips_lite(tokens)` | Mini touch line | `SFeedScripLite` |
| `subscribe_depth(tokens)` | Depth | `SFeedScrip` with `buy`/`sell` rows |
| `subscribe_full_depth(tokens)` | Full depth | `SFeedScrip` with `buy`/`sell` rows |
| `subscribe_index(tokens)` | Index | `SFeedIndex` |

### LTP (single instrument)

```python
await ws.subscribe_scrips([WsToken("nse_cm", "Nifty 50")])
```

### Option chain (batched)

All tokens are sent in a single frame (`inputtoken` becomes a comma-separated list):

```python
chain = [WsToken("nse_fo", str(t)) for t in range(44498, 44520)]
await ws.subscribe_scrips(chain)
```

### Subscription limit

At most **3000 input tokens** may be subscribed at once, counted as a running total
across all subscribe requests (LTP, option chain, index, depth, ...). A request that
would exceed the limit raises `SubscriptionError` and sends nothing. Use
`ws.subscription_count` to check current usage; configure the cap with
`max_subscriptions` (see the [SFeed guide](../../guides/websocket.md#configuration)).

## Unsubscribe

Each subscribe method has a matching `unsubscribe_*`. All tokens are sent in a single
batched frame.

```python
tokens = [WsToken("nse_cm", "11536"), WsToken("nse_cm", "Nifty 50")]

await ws.subscribe_scrips(tokens)
# ... receive data ...
await ws.unsubscribe_scrips(tokens)
```

| Method | Stops |
|--------|-------|
| `unsubscribe_scrips(tokens)` | Touch-line feed |
| `unsubscribe_scrips_lite(tokens)` | Mini touch-line feed |
| `unsubscribe_depth(tokens)` | Depth feed |
| `unsubscribe_full_depth(tokens)` | Full-depth feed |
| `unsubscribe_index(tokens)` | Index feed |

### LTP (single instrument)

```python
await ws.unsubscribe_scrips([WsToken("nse_cm", "Nifty 50")])
```

On the wire the unsubscribe frame omits the `json` field:
`{"event": "unsubscribeScrips", "inputtoken": "nse_cm|Nifty 50"}`.

### Option chain (batched)

```python
chain = [WsToken("nse_fo", str(t)) for t in range(44498, 44520)]
await ws.unsubscribe_scrips(chain)  # one batched frame
```

## Parameters

| Name | Description | Type |
|------|-------------|------|
| `tokens` | List of `WsToken(exchange_segment, instrument_token)` | `list[WsToken]` |

### Exchange segments

`nse_cm`, `bse_cm`, `nse_fo`, `bse_fo`, `cde_fo`, `mcx_fo` (see the guide for the full enum).

### Index tokens

For indices, use the index name as the token, e.g.
`WsToken("nse_cm", "Nifty 50")`, `WsToken("nse_cm", "Nifty Bank")`, `WsToken("bse_cm", "SENSEX")`.

## Return type

Messages are typed Pydantic models (`SFeedScrip`, `SFeedScripLite`, `SFeedIndex`,
`SFeedMarketStatus`). All prices are pre-scaled by the per-exchange divider. Call
`message.model_dump()` for a dict.

Every message includes `exchange_segment`, `instrument_token`, and
`trading_symbol`. The `trading_symbol` (e.g. `"RELIANCE-EQ"`) is resolved from the
subscribe acknowledgement and is `None` until that ack arrives or if the server
returned no symbol for the token. See the
[Trading symbol](../../guides/websocket.md#trading-symbol) section of the guide.

## Complete example (subscribe → receive → unsubscribe)

```python
import asyncio
from neo_api_client import NeoAPI
from neo_api_client.websocket.feed import WsToken


async def main():
    client = NeoAPI(environment="prod", consumer_key="your-consumer-key")
    client.totp_login(mobile_number="+919876543210", ucc="YOUR_UCC", totp="123456")
    client.totp_validate(mpin="123456")

    tokens = [WsToken("nse_cm", "11536")]

    async with client.create_websocket() as ws:
        await ws.subscribe_scrips(tokens)

        # Read a bounded window of messages, then unsubscribe
        try:
            async with asyncio.timeout(5):
                async for message in ws:
                    print(message.last_traded_price)
        except TimeoutError:
            pass

        await ws.unsubscribe_scrips(tokens)
    # Leaving the `async with` block closes the connection automatically.


asyncio.run(main())
```

## Notes

- Unsubscribing does **not** close the connection — you can keep subscribing to other
  instruments; exiting the `async with` block (or calling `await ws.close()`) closes it.
- Unsubscribing from a non-subscribed instrument is harmless.

## Related

- [Order Feed](./order_feed.md) — Order & position updates (separate WebSocket)
- [SFeed WebSocket Guide](../../guides/websocket.md) — full client reference

[[Back to top]](#) [[Back to SFeed guide]](../../guides/websocket.md) [[Back to README]](../../../README.md)
