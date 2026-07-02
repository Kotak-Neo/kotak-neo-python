# WebSocket — Unsubscribe (SFeed)

Stop receiving live market data for the given instruments on the async/await
**SFeed** WebSocket client (v2.2.0+). The legacy `client.un_subscribe(...)` API was
**removed in v2.2.0** and now raises `NotImplementedError`.

> Full reference: **[SFeed WebSocket Guide](../../guides/websocket.md)**

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
await ws.unsubscribe_scrips(chain)   # one batched frame
```

## Parameters

| Name | Description | Type |
|------|-------------|------|
| `tokens` | List of `WsToken(exchange_segment, instrument_token)` to unsubscribe | `list[WsToken]` |

## Complete Example

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

- [Subscribe](./subscribe.md) — Subscribe to live market feed
- [Order Feed](./order_feed.md) — Order updates status

[[Back to top]](#) [[Back to SFeed guide]](../../guides/websocket.md) [[Back to README]](../../../README.md)
