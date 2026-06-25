# **webSocket_Orderfeed**

```python

client.subscribe_to_orderfeed()
```

### Example

```python
from neo_api_client import NeoAPI


def on_message(message):
    print('[Res]: ', message)

def on_error(message):
    result = message
    print('[OnError]: ', result)

def on_open(message):
    print('[OnOpen]: ', message)

def on_close(message):
    print('[OnClose]: ', message)

client = NeoAPI(environment='prod', access_token=None, neo_fin_key=None)
client.totp_login(mobilenumber="", ucc="", totp='')
client.totp_validate(mpin="")

# Setup Callbacks for websocket events (Optional)
client.on_message = on_message  # called when message is received from websocket
client.on_error = on_error  # called when any error or exception occurs in code or websocket
client.on_close = on_close  # called when websocket connection is closed
client.on_open = on_open  # called when websocket successfully connects

try:
    # Get live feed data
    client.subscribe_to_orderfeed()
except Exception as e:
    print("Exception while connection to orderfeed socket->subscribe_to_orderfeed: %s\n" % e)

```

### Return type

**object**

### Sample response

```python
{
    #Gets live data
}
```

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)  [[Back to README]](../README.md)
