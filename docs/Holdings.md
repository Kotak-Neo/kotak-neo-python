# **Holdings**
Get your current holdings

```python
client.holdings("")
```

### Example

```python

from neo_api_client import NeoAPI


#First initialize session and generate session token
client = NeoAPI(environment='prod', access_token=None, neo_fin_key=None)
client.totp_login(mobilenumber="", ucc="", totp='')
client.totp_validate(mpin="")

try:
    client.holdings("")
except Exception as e:
    print("Exception when calling Holdings->holdings: %s\n" % e)
```

### Return type

**object**

### Sample response
```json
{
    "data": [
        {
            "displaySymbol": "IDEA",
            "averagePrice": 9.5699,
            "quantity": 35,
            "exchangeSegment": "nse_cm",
            "exchangeIdentifier": "14366",
            "holdingCost": 334.9475,
            "mktValue": 327.6,
            "scripId": "746a0ebbc6295a002ab27e42a3e06a6792baeba1",
            "instrumentToken": 8658,
            "instrumentType": "Equity",
            "isAlternateScrip": false,
            "closingPrice": 9.36,
            "symbol": "IDEA",
            "sellableQuantity": 35
        }
    ]
}

```

### HTTP request headers

 - **Accept**: application/json


### HTTP response details
| Status Code | Description                                           |
|-------------|-------------------------------------------------------|
| *200*       | Gets the Portfolio holdings data for a client account |
| *400*       | Invalid or missing input parameters                   |
| *403*       | Invalid session, please re-login to continue          |
| *429*       | Too many requests to the API                          |
| *500*       | Unexpected error                                      |
| *502*       | Not able to communicate with OMS                      |
| *503*       | Trade API service is unavailable                      |
| *504*       | Gateway timeout, trade API is unreachable             |
