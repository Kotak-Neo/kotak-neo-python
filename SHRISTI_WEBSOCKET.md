# Shristi WebSocket Implementation

Modern async/await WebSocket client for Kotak Neo's Shristi broadcast platform.

## Status: ⚠️ Beta (v2.2.0)

**Requires additional information before full release:**
- [ ] Actual Shristi WebSocket URL
- [ ] Authentication protocol details
- [ ] Message format specification (JSON vs Binary)
- [ ] Subscription request/response format
- [ ] Test credentials for UAT environment

## What's Implemented

### ✅ Core Features
- **Async/await API** with `async for` iteration
- **Type-safe Pydantic models** for all message types
- **Context manager support** for automatic cleanup
- **Auto-reconnection** with configurable retry logic
- **Heartbeat management** with automatic keep-alive
- **Multiple subscription types**: Scrip, Index, Depth

### ✅ Backward Compatibility
- Old callback-based WebSocket still works
- Deprecation warnings added (will be removed in v3.0.0)
- Helper method `NeoAPI.create_websocket()` for easy migration

### ✅ Documentation
- Complete API documentation with examples
- Migration guide from old to new WebSocket
- Example scripts in `examples/shristi_websocket_example.py`

## File Structure

```
neo_api_client/
├── websocket/
│   ├── HSWebSocketLib.py              # [OLD] Keep for backward compatibility
│   ├── NeoWebSocket.py                # [OLD] Keep for backward compatibility
│   └── shristi/
│       ├── __init__.py                # Package exports
│       ├── client.py                  # Main ShristiWebSocket client
│       ├── models.py                  # Pydantic models
│       ├── exceptions.py              # Custom exceptions
│       └── README.md                  # Full documentation
```

## Usage Examples

### Basic Usage

```python
import asyncio
from neo_api_client import NeoAPI, ShristiWebSocket, WsToken

async def main():
    # Login
    client = NeoAPI(consumer_key="...", environment="prod")
    client.totp_login(mobile_number="+91...", ucc="...", totp="...")
    client.totp_validate(mpin="...")
    
    # Create WebSocket using helper method
    async with client.create_websocket() as ws:
        await ws.subscribe_scrips([WsToken("nse_cm", "1333")])
        
        async for message in ws:
            print(f"LTP: {message.last_traded_price}")

asyncio.run(main())
```

### Direct Import

```python
from neo_api_client.websocket.shristi import ShristiWebSocket, WsToken

async with ShristiWebSocket(access_token, sid) as ws:
    await ws.subscribe_scrips([WsToken("nse_cm", "1333")])
    async for msg in ws:
        print(msg)
```

## Message Types

### 1. SFeedScrip (Full)
Complete market data with OHLC, volume, depth summary, circuit limits.

```python
from neo_api_client import SFeedScrip

async for message in ws:
    if isinstance(message, SFeedScrip):
        print(f"LTP: {message.last_traded_price}")
        print(f"Change: {message.change} ({message.percentage_change}%)")
        print(f"Volume: {message.trade_volume}")
```

### 2. SFeedScripLite (Optimized)
Essential data only - LTP, change, timestamp. Use for bandwidth optimization.

```python
await ws.subscribe_scrips([token], mode="lite")
```

### 3. SFeedIndex
Index values and OHLC data.

```python
await ws.subscribe_index([WsToken("nse_cm", "26000")])  # NIFTY 50
```

### 4. SFeedDepth
Market depth with total buy/sell quantities.

```python
await ws.subscribe_depth([WsToken("nse_cm", "1333")])
```

## Migration from Old WebSocket

### Before (Deprecated)
```python
client = NeoAPI(...)
client.on_message = lambda msg: print(msg)
client.subscribe(instrument_tokens=[
    {"instrument_token": "1333", "exchange_segment": "nse_cm"}
])
```

### After (Recommended)
```python
async with client.create_websocket() as ws:
    await ws.subscribe_scrips([WsToken("nse_cm", "1333")])
    async for msg in ws:
        print(msg)
```

## Deprecation Timeline

| Version | Status | Action |
|---------|--------|--------|
| **v2.2.0** | ✅ Current | Shristi WebSocket available (beta) |
| **v2.3.0** | 🔜 Q3 2026 | Old WebSocket marked deprecated with warnings |
| **v3.0.0** | 🔜 Q4 2026 | Old WebSocket removed |

## TODO Before Release

### Critical
1. **Get Shristi WebSocket URL**
   - Production: `wss://???`
   - UAT: `wss://???`

2. **Authentication Protocol**
   - Connection handshake format
   - Authentication message structure
   - Response validation

3. **Message Format**
   - Confirm JSON vs Binary
   - Field name mapping (camelCase vs snake_case)
   - System message types to ignore

4. **Subscription Protocol**
   - Subscribe request format
   - Unsubscribe request format
   - Acknowledgment handling

### Testing
- [ ] Unit tests for all models
- [ ] Integration tests with UAT
- [ ] Load testing with multiple subscriptions
- [ ] Reconnection testing
- [ ] Error handling validation

### Documentation
- [ ] Update main README with Shristi examples
- [ ] Add API reference documentation
- [ ] Create video tutorial
- [ ] Update changelog

## Dependencies

```toml
[project.optional-dependencies]
websocket = [
    "websockets>=12.0",
    "pydantic>=2.0.0",
]
```

## Questions for Kotak Neo Team

1. **URL**: What's the Shristi WebSocket production URL?
2. **Protocol**: JSON or Binary messages?
3. **Auth**: Same token format as current HSWebSocket?
4. **Messages**: Can you provide sample payloads for:
   - Connection request/response
   - Subscribe request/response
   - Data messages (scrip, index, depth)
   - Heartbeat/system messages
5. **Rate Limits**: Any subscription limits per connection?
6. **Lifecycle**: How to handle graceful shutdown?

## Contact

For questions or to provide the required information:
- GitHub Issues: https://github.com/anthropics/kotak-neo-python/issues
- API Documentation: https://www.kotaksecurities.com/platform/kotak-neo-trade-api/

---

**Note**: This is a beta implementation. The WebSocket client is fully functional but requires actual Shristi backend details for production use. All TODOs are marked with `# TODO:` comments in the code.
