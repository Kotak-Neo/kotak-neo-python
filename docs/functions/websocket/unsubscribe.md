# Unsubscribe

Stop receiving live market data updates for specified instruments.

## Function Signature

```python
client.un_subscribe(
    instrument_tokens,
    isIndex=False,
    isDepth=False
)
```

## Description

The `un_subscribe()` function unsubscribes from live market data feeds for the specified instruments. After unsubscribing, you will no longer receive real-time updates for those instruments via WebSocket.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `instrument_tokens` | list | Yes | List of instrument dictionaries to unsubscribe |
| `isIndex` | bool | No | Whether instruments are indices (default: False) |
| `isDepth` | bool | No | Whether depth data was subscribed (default: False) |

### Instrument Token Format

```python
[
    {
        "instrument_token": "1333",
        "exchange_segment": "nse_cm"
    }
]
```

## Return Type

**None** - Prints confirmation message

## Example

### Basic Usage

```python
from neo_api_client import NeoAPI

# Initialize and login
client = NeoAPI(environment='prod', consumer_key='your-consumer-key')
client.totp_login(mobile_number='+919876543210', ucc='YOUR_UCC', totp='123456')
client.totp_validate(mpin='123456')

# Setup callbacks
client.on_message = lambda msg: print(f"Message: {msg}")
client.on_error = lambda err: print(f"Error: {err}")
client.on_open = lambda: print("Connected")
client.on_close = lambda: print("Disconnected")

# Subscribe to instruments
instrument_tokens = [
    {
        "instrument_token": "1333",
        "exchange_segment": "nse_cm"
    },
    {
        "instrument_token": "2885",
        "exchange_segment": "nse_cm"
    }
]

client.subscribe(instrument_tokens=instrument_tokens, isIndex=False, isDepth=False)

# ... Receive live data ...

# Unsubscribe when done
try:
    client.un_subscribe(
        instrument_tokens=instrument_tokens,
        isIndex=False,
        isDepth=False
    )
    print("Successfully unsubscribed")
except Exception as e:
    print(f"Exception when calling un_subscribe: {e}")
```

### Unsubscribe Single Instrument

```python
# Unsubscribe from single stock
client.un_subscribe(
    instrument_tokens=[
        {
            "instrument_token": "1333",
            "exchange_segment": "nse_cm"
        }
    ],
    isIndex=False,
    isDepth=False
)
```

### Unsubscribe Index

```python
# Unsubscribe from index
client.un_subscribe(
    instrument_tokens=[
        {
            "instrument_token": "26000",  # NIFTY 50
            "exchange_segment": "nse_cm"
        }
    ],
    isIndex=True,
    isDepth=False
)
```

## Response

### Console Output

```
The Data has been Un-Subscribed
```

### WebSocket Message

After unsubscribing, you'll receive a confirmation message via the `on_message` callback:

```json
"Un-Subscribed Successfully!"
```

### After Unsubscribe

No more real-time updates will be received for the unsubscribed instruments.

## Error Handling

### Pre-Login Error

```python
ValueError: Please complete the Login Flow to Un_Subscribe the Scrips
```

### Invalid Instrument

If you try to unsubscribe from an instrument that wasn't subscribed, the operation completes silently without error.

## Exchange Segments

| Segment | Description |
|---------|-------------|
| `nse_cm` | NSE Cash Market |
| `bse_cm` | BSE Cash Market |
| `nse_fo` | NSE Futures & Options |
| `bse_fo` | BSE Futures & Options |
| `cde_fo` | Currency Derivatives |
| `mcx_fo` | MCX Commodities |

## Performance

- **Average Latency**: 3-5 seconds (includes confirmation wait time)
- **Operation**: Asynchronous

## Notes

- Always unsubscribe from instruments before closing your application
- Unsubscribing doesn't close the WebSocket connection - you can subscribe to other instruments
- Use the same `isIndex` and `isDepth` values that were used during subscription
- Unsubscribing from non-subscribed instruments is harmless

## Complete Example

```python
import time
from neo_api_client import NeoAPI

client = NeoAPI(environment='prod', consumer_key='your-consumer-key')

# Login
client.totp_login(mobile_number='+919876543210', ucc='YOUR_UCC', totp='123456')
client.totp_validate(mpin='123456')

# Setup callbacks
received_messages = []
client.on_message = lambda msg: received_messages.append(msg)
client.on_error = lambda err: print(f"Error: {err}")
client.on_open = lambda: print("WebSocket opened")
client.on_close = lambda: print("WebSocket closed")

# Subscribe
instruments = [
    {"instrument_token": "1333", "exchange_segment": "nse_cm"}
]

client.subscribe(instrument_tokens=instruments)

# Wait for data
time.sleep(5)
print(f"Received {len(received_messages)} messages")

# Unsubscribe
client.un_subscribe(instrument_tokens=instruments)

# Wait to confirm no more messages
time.sleep(3)

# Close WebSocket
if client.NeoWebSocket and client.NeoWebSocket.hsWebsocket:
    client.NeoWebSocket.hsWebsocket.close()

# Logout
client.logout()
```

## Related Functions

- [Subscribe](./subscribe.md) - Subscribe to live market feed
- [Order Feed](./order_feed.md) - Subscribe to order updates

## Best Practices

1. **Always unsubscribe** when you no longer need data
2. **Match parameters** - Use same isIndex/isDepth as subscription
3. **Handle cleanup** - Unsubscribe before closing application
4. **Resource management** - Unsubscribe to free up bandwidth

```python
# Good practice: cleanup in finally block
try:
    client.subscribe(instrument_tokens=instruments)
    # ... your code ...
finally:
    client.un_subscribe(instrument_tokens=instruments)
    if client.NeoWebSocket:
        client.NeoWebSocket.hsWebsocket.close()
    client.logout()
```

[[Back to top]](#) [[Back to API list]](../README.md) [[Back to README]](../../../README.md)
