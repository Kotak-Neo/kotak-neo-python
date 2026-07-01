# Shristi WebSocket Client

Modern async/await WebSocket client for Kotak Neo's Shristi broadcast platform.

## Features

- ✅ **Async/await API** - Modern Python asyncio support
- ✅ **Type-safe** - Pydantic models with full type hints
- ✅ **Async iteration** - Use `async for` to process messages
- ✅ **Context manager** - Automatic connection management
- ✅ **Auto-reconnect** - Automatic reconnection on disconnect
- ✅ **Heartbeat** - Built-in heartbeat management
- ✅ **Multiple feed types** - Scrip, Index, Depth data

## Installation

Requires Python 3.10+ with `websockets` and `pydantic`:

```bash
pip install kotakneoapi[websocket]
```

## Quick Start

### Async/Await API (Recommended)

```python
import asyncio
from neo_api_client import NeoAPI
from neo_api_client.websocket.shristi import ShristiWebSocket, WsToken

async def main():
    # Initialize client
    client = NeoAPI(
        consumer_key="your-consumer-key",
        environment="prod"
    )
    
    # Login
    client.totp_login(
        mobile_number="+919876543210",
        ucc="ABC123",
        totp="123456"
    )
    client.totp_validate(mpin="123456")
    
    # Create WebSocket connection
    async with ShristiWebSocket(
        access_token=client.configuration.edit_token,
        sid=client.configuration.edit_sid
    ) as ws:
        # Subscribe to scrips
        await ws.subscribe_scrips([
            WsToken("nse_cm", "1333"),   # RELIANCE
            WsToken("nse_cm", "11536"),  # TCS
        ])
        
        # Process messages
        async for message in ws:
            print(f"{type(message).__name__}: {message.last_traded_price}")

asyncio.run(main())
```

### Without Context Manager

```python
async def main():
    ws = ShristiWebSocket(access_token, sid)
    
    try:
        await ws.connect()
        await ws.subscribe_scrips([WsToken("nse_cm", "1333")])
        
        async for message in ws:
            print(message.model_dump())
            
    finally:
        await ws.close()
```

### Callback-based API (Backward Compatible)

```python
async def main():
    ws = ShristiWebSocket(access_token, sid)
    
    # Set callbacks
    def on_message(msg):
        print(f"Received: {msg}")
    
    ws.on_message = on_message
    ws.on_error = lambda e: print(f"Error: {e}")
    
    await ws.connect()
    await ws.subscribe_scrips([WsToken("nse_cm", "1333")])
    
    # Keep running
    await asyncio.Event().wait()
```

## Message Types

### Full Scrip Data

```python
from neo_api_client.websocket.shristi import SFeedScrip

async for message in ws:
    if isinstance(message, SFeedScrip):
        print(f"LTP: {message.last_traded_price}")
        print(f"Change: {message.change} ({message.percentage_change}%)")
        print(f"Volume: {message.trade_volume}")
        print(f"OHLC: {message.open_price}/{message.high_price}/"
              f"{message.low_price}/{message.close_price}")
```

### Lite Scrip Data (Bandwidth Optimized)

```python
await ws.subscribe_scrips([WsToken("nse_cm", "1333")], mode="lite")

async for message in ws:
    if isinstance(message, SFeedScripLite):
        print(f"LTP: {message.last_traded_price}")
```

### Index Data

```python
await ws.subscribe_index([WsToken("nse_cm", "26000")])  # NIFTY 50

async for message in ws:
    if isinstance(message, SFeedIndex):
        print(f"Index: {message.last_traded_price}")
```

### Market Depth

```python
await ws.subscribe_depth([WsToken("nse_cm", "1333")])

async for message in ws:
    if isinstance(message, SFeedDepth):
        print(f"Buy Qty: {message.total_buy_qty}")
        print(f"Sell Qty: {message.total_sell_qty}")
```

## Advanced Usage

### Multiple Subscriptions

```python
# Subscribe to different types
await ws.subscribe_scrips([WsToken("nse_cm", "1333")])
await ws.subscribe_index([WsToken("nse_cm", "26000")])
await ws.subscribe_depth([WsToken("nse_cm", "11536")])

async for message in ws:
    match message:
        case SFeedScrip():
            print(f"Scrip: {message.last_traded_price}")
        case SFeedIndex():
            print(f"Index: {message.last_traded_price}")
        case SFeedDepth():
            print(f"Depth: {message.total_buy_qty}")
```

### Unsubscribe

```python
tokens = [WsToken("nse_cm", "1333")]

await ws.subscribe_scrips(tokens)
# ... do something ...
await ws.unsubscribe_scrips(tokens)
```

### Custom Reconnection

```python
ws = ShristiWebSocket(
    access_token=token,
    sid=sid,
    reconnect_delay=10,  # Wait 10 seconds before reconnecting
    max_reconnect_attempts=10  # Try 10 times
)
```

### Connection Event Handlers

```python
def on_connect():
    print("Connected!")

def on_disconnect():
    print("Disconnected!")

def on_error(error):
    print(f"Error: {error}")

ws.on_connect = on_connect
ws.on_disconnect = on_disconnect
ws.on_error = on_error

await ws.connect()
```

## Comparing with Old WebSocket

### Old (Callback-based)

```python
client = NeoAPI(...)
client.login(...)

# Set callback
def on_message(message):
    print(message)

client.on_message = on_message

# Subscribe
client.subscribe(
    instrument_tokens=[
        {"instrument_token": "1333", "exchange_segment": "nse_cm"}
    ]
)

# Blocks forever
```

### New (Async/await)

```python
client = NeoAPI(...)
client.login(...)

async with ShristiWebSocket(...) as ws:
    await ws.subscribe_scrips([WsToken("nse_cm", "1333")])
    
    async for message in ws:
        print(message)
```

## Migration Guide

### Step 1: Update Code to Async

**Before:**
```python
def main():
    client = NeoAPI(...)
    client.on_message = callback
    client.subscribe(...)
```

**After:**
```python
async def main():
    async with ShristiWebSocket(...) as ws:
        await ws.subscribe_scrips(...)
        async for msg in ws:
            process(msg)

asyncio.run(main())
```

### Step 2: Update Message Handling

**Before:**
```python
def on_message(message):
    if message["type"] == "quotes":
        ltp = message["data"]["ltp"]
```

**After:**
```python
async for message in ws:
    if isinstance(message, SFeedScrip):
        ltp = message.last_traded_price
```

### Step 3: Update Subscription Format

**Before:**
```python
client.subscribe(instrument_tokens=[
    {"instrument_token": "1333", "exchange_segment": "nse_cm"}
])
```

**After:**
```python
await ws.subscribe_scrips([
    WsToken("nse_cm", "1333")
])
```

## Error Handling

```python
from neo_api_client.websocket.shristi.exceptions import (
    ConnectionError,
    AuthenticationError,
    SubscriptionError,
)

try:
    async with ShristiWebSocket(...) as ws:
        await ws.subscribe_scrips([WsToken("nse_cm", "1333")])
        
        async for message in ws:
            print(message)
            
except ConnectionError as e:
    print(f"Connection failed: {e}")
except AuthenticationError as e:
    print(f"Auth failed: {e}")
except SubscriptionError as e:
    print(f"Subscription failed: {e}")
```

## Performance Tips

1. **Use lite mode** for bandwidth optimization:
   ```python
   await ws.subscribe_scrips(tokens, mode="lite")
   ```

2. **Process messages in batches**:
   ```python
   async def batch_processor():
       batch = []
       async for message in ws:
           batch.append(message)
           if len(batch) >= 100:
               await process_batch(batch)
               batch.clear()
   ```

3. **Use type checking** for filtering:
   ```python
   async for message in ws:
       if isinstance(message, SFeedScrip):
           # Only process scrip messages
           await process_scrip(message)
   ```

## Deprecation Notice

The old callback-based WebSocket (`NeoAPI.subscribe()`) will be:
- ⚠️ **Deprecated in v2.3.0** (with warnings)
- ❌ **Removed in v3.0.0**

Please migrate to `ShristiWebSocket` for new projects.
