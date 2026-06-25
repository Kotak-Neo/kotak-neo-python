# **Quotes**

Quotes API can be accessed by access token without completing login.instrument_tokens: This is a list of dictionaries.
    # instrument_token: The instrument token of the stock
    # exchange_segment: Expected values are nse_cm, bse_cm, nse_fo, bse_fo, cde_fo
```python
client.quotes_neo_symbol(neo_symbol = neo_symbol, quote_type = "")
```
### Example

```python

from neo_api_client import NeoAPI

#Only need to initialize session and generate session token

client = NeoAPI(environment='prod', access_token=None, neo_fin_key=None)

instrument_tokens = [
    {"instrument_token": "Nifty 50", "exchange_segment": "nse_cm"},
    {"instrument_token": "Nifty Bank", "exchange_segment": "nse_cm"}
]

try:
    client.quotes(instrument_tokens = instrument_tokens, quote_type = "all")
except Exception as e:
    print("Exception when calling Quotes Api->quotes: %s\n" % e)
```

### Parameters

| Name                | Description                                                                         | Type |
|---------------------|-------------------------------------------------------------------------------------|------|
| *instrument_tokens*  | This is a list of dictionaries                                                      | List |
| *quote_type*  | all, depth, ohlc, ltp, oi, 52w, circuit_limits, scrip_details (Default value - all) | Str  |

### Return type

**object**

### HTTP request headers

 - **Accept**: application/json


### HTTP response details
| Status Code | Description                                  |
|-------------|----------------------------------------------|
| *200*       | Ok                                           |
| *400*       | Invalid or missing input parameters          |
| *403*       | Invalid session, please re-login to continue |
| *429*       | Too many requests to the API                 |
| *500*       | Unexpected error                             |
| *502*       | Not able to communicate with OMS             |
| *503*       | Trade API service is unavailable             |
| *504*       | Gateway timeout, trade API is unreachable    |
