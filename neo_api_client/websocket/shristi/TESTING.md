# Testing Shristi WebSocket

## Installation

```bash
# Install with Shristi WebSocket support
pip install kotakneoapi[shristi]

# Or install dependencies manually
pip install websockets>=12.0 pydantic>=2.0.0
```

## Quick Test

```python
import asyncio
from neo_api_client import NeoAPI
from neo_api_client.websocket.shristi import ShristiWebSocket, WsToken

async def test_websocket():
    # 1. Login
    client = NeoAPI(
        consumer_key="your-consumer-key",
        environment="uat"  # Use UAT for testing
    )
    
    client.totp_login(
        mobile_number="+91XXXXXXXXXX",
        ucc="YOUR_UCC",
        totp="XXXXXX"
    )
    
    client.totp_validate(mpin="XXXXXX")
    
    print("✓ Logged in")
    
    # 2. Create WebSocket
    async with client.create_websocket() as ws:
        print("✓ Connected to WebSocket")
        
        # 3. Subscribe
        await ws.subscribe_scrips([
            WsToken("nse_cm", "1333"),  # RELIANCE
        ])
        print("✓ Subscribed")
        
        # 4. Receive messages
        count = 0
        async for message in ws:
            print(f"Received: {type(message).__name__} - LTP: {message.last_traded_price}")
            count += 1
            if count >= 10:
                break
        
        print(f"✓ Received {count} messages")

if __name__ == "__main__":
    asyncio.run(test_websocket())
```

## Expected Issues (Until Shristi URL is updated)

### 1. Connection Error
```
ConnectionError: Failed to connect: ...
```
**Why**: Using placeholder URL `wss://mlhsm.kotaksecurities.com`
**Fix**: Need actual Shristi WebSocket URL

### 2. Authentication Error
```
AuthenticationError: Authentication failed: ...
```
**Why**: Auth protocol may differ from placeholder
**Fix**: Need actual auth message format

### 3. Message Parse Error
```
MessageParseError: Invalid message format: ...
```
**Why**: Field names/format may differ
**Fix**: Need actual message samples

## Debugging

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now run your code
async with client.create_websocket() as ws:
    # Will show detailed connection info
    ...
```

Check connection manually:

```python
ws = ShristiWebSocket(access_token, sid)

try:
    await ws.connect()
    print(f"Connected: {ws.is_connected}")
    print(f"Authenticated: {ws._authenticated}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
```

## Testing Checklist

Once Shristi details are available:

- [ ] Connection succeeds
- [ ] Authentication succeeds
- [ ] Subscribe to scrip works
- [ ] Receive scrip messages
- [ ] Message parsing works
- [ ] Unsubscribe works
- [ ] Reconnection works
- [ ] Heartbeat works
- [ ] Multiple subscriptions work
- [ ] Index subscription works
- [ ] Depth subscription works
- [ ] Error handling works
- [ ] Graceful shutdown works

## Unit Tests

Create tests in `tests/unit/test_shristi_websocket.py`:

```python
import pytest
from neo_api_client.websocket.shristi import WsToken, SFeedScrip

def test_wstoken_creation():
    token = WsToken("nse_cm", "1333")
    assert token.exchange_segment == "nse_cm"
    assert token.instrument_token == "1333"

def test_wstoken_immutable():
    token = WsToken("nse_cm", "1333")
    with pytest.raises(Exception):
        token.exchange_segment = "bse_cm"  # Should fail

def test_sfeed_scrip_parsing():
    data = {
        "type": "scrip",
        "exchangeSegment": "nse_cm",
        "token": "1333",
        "lastTradedPrice": 2500.50,
        "change": 25.50,
        "percentageChange": 1.03,
        # ... other fields
    }
    
    message = SFeedScrip(**data)
    assert message.last_traded_price == 2500.50
    assert message.exchange_segment == "nse_cm"
```

Run tests:

```bash
pytest tests/unit/test_shristi_websocket.py -v
```

## Integration Tests

Create tests in `tests/integration/test_shristi_integration.py`:

```python
import asyncio
import pytest
from neo_api_client import NeoAPI

@pytest.mark.asyncio
async def test_websocket_connection():
    """Test WebSocket connection and basic subscription."""
    client = NeoAPI(consumer_key="...", environment="uat")
    # Login...
    
    async with client.create_websocket() as ws:
        assert ws.is_connected
        
        await ws.subscribe_scrips([WsToken("nse_cm", "1333")])
        
        # Receive at least one message
        message = await ws.__anext__()
        assert message is not None

@pytest.mark.asyncio
async def test_reconnection():
    """Test automatic reconnection."""
    # ... test reconnection logic
```

Run integration tests (requires credentials):

```bash
pytest tests/integration/test_shristi_integration.py -v
```

## Load Testing

Test with multiple subscriptions:

```python
async def load_test():
    async with client.create_websocket() as ws:
        # Subscribe to 100 tokens
        tokens = [WsToken("nse_cm", str(i)) for i in range(1333, 1433)]
        await ws.subscribe_scrips(tokens)
        
        # Receive messages for 1 minute
        start = time.time()
        count = 0
        
        async for message in ws:
            count += 1
            if time.time() - start > 60:
                break
        
        print(f"Received {count} messages in 60 seconds")
        print(f"Rate: {count/60:.2f} messages/second")
```

## Performance Testing

```python
import time

async def perf_test():
    async with client.create_websocket() as ws:
        await ws.subscribe_scrips([WsToken("nse_cm", "1333")])
        
        latencies = []
        async for message in ws:
            # Assuming message has timestamp
            latency = time.time() - message.last_trade_time
            latencies.append(latency)
            
            if len(latencies) >= 1000:
                break
        
        print(f"Avg latency: {sum(latencies)/len(latencies):.2f}s")
        print(f"Min latency: {min(latencies):.2f}s")
        print(f"Max latency: {max(latencies):.2f}s")
```

## Questions to Answer During Testing

1. **Connection**
   - Does it connect successfully?
   - How long does connection take?
   - Any SSL certificate issues?

2. **Authentication**
   - Does auth work with existing tokens?
   - What's the response format?
   - Any additional steps needed?

3. **Messages**
   - What's the actual message format (JSON/Binary)?
   - Are field names camelCase or snake_case?
   - What system messages need to be ignored?

4. **Subscriptions**
   - Does subscribe return acknowledgment?
   - What's the max subscriptions per connection?
   - Can you subscribe to multiple types simultaneously?

5. **Reconnection**
   - Does auto-reconnect work?
   - Are subscriptions maintained?
   - Any data loss during reconnection?

6. **Performance**
   - What's the message rate?
   - Any throttling limits?
   - Memory usage with many subscriptions?

## Contact

Report issues or provide feedback:
- File structure looks good
- Code follows best practices
- Ready for testing once Shristi details are available
