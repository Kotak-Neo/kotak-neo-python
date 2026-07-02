# WebSocket — Order Feed

> **Removed in v2.2.0.** `client.subscribe_to_orderfeed()` was part of the legacy
> callback-based WebSocket, which has been replaced by the async/await **SFeed**
> client. Calling it now raises `NotImplementedError`.

The SFeed feed documented here covers **market data** (touch line, depth, index).
For live market data see:

- **[Subscribe](./subscribe.md)** — subscribe to the live market feed
- **[Unsubscribe](./unsubscribe.md)** — stop the feed
- **[SFeed WebSocket Guide](../../guides/websocket.md)** — full API, message
  types, configuration, and migration reference

If a dedicated order-update stream becomes available on the SFeed platform, it will be
documented here.

[[Back to top]](#) [[Back to SFeed guide]](../../guides/websocket.md) [[Back to README]](../../../README.md)
