# **Margin_Required**
Get required margin details

```python
client.margin_required(exchange_segment = "", price = "", order_type= "", product = "", quantity = "", instrument_token = "",
                       transaction_type = "")
```

### Example

```python
from neo_api_client import NeoAPI


#First initialize session and generate session token
client = NeoAPI(environment='prod', access_token=None, neo_fin_key=None)
client.totp_login(mobilenumber="", ucc="", totp='')
client.totp_validate(mpin="")

try:
    client.margin_required(exchange_segment = "", price = "", order_type= "", product = "",   quantity = "", instrument_token = "",  transaction_type = "")
except Exception as e:
    print("Exception when calling margin_required->margin_required: %s\n" % e)
```

### Parameters

| Name               | Description                                                                                                              | Type           |
|--------------------|--------------------------------------------------------------------------------------------------------------------------|----------------|
| *exchange_segment* | nse_cm - NSE<br/>bse_cm - BSE<br/>nse_fo - NFO<br/>bse_fo - BFO<br/>cde_fo - CDS<br/>mcx_fo - MCX                        | Str            |
| *price*            | Price of the order                                                                                                       | Str            |
| *order_type*       | L - Limit<br/>MKT - Market<br/>SL - Stop loss limit<br/>SL-M - Stop loss market                                          | Str            |
| *product*          | NRML - Normal<br/>CNC - Cash and Carry<br/>MIS - MIS<br/>INTRADAY - INTRADAY<br/>CO - Cover Order              | Str            |
| *quantity*         | Quantity of the order                                                                                    | Str            |
| *instrument_token* | pSymbol in ScripMaster files                                                                                              | Str            |
| *transaction_type* | B(Buy), S(sell)                                                                                                          | Str            |
| *trading_symbol*   | pTrdSymbol in ScripMaster files                                                                                  | Str            |
| *transaction_type* | B(Buy), S(sell)                                                                                                          | Str            |
| *trigger_price*    | Optional, required for stop loss and cover order                                                    | Str        |


### Return type

**object**

### Sample response

```json
{
    "data": {
        "avlCash": "38.190000",
        "totMrgnUsd": "34.280000",
        "mrgnUsd": "18.780000",
        "ordMrgn": "15.500000",
        "rmsVldtd": "OK",
        "reqdMrgn": "0.000000",
        "avlMrgn": "0.000000",
        "insufFund": "0.000000",
        "stat": "Ok",
        "stCode": 200
    }
}
```

### HTTP request headers

 - **Accept**: application/json

### HTTP response details
| Status Code | Description                                           |
|-------------|-------------------------------------------------------|
| *200*       | Gets the margin_required data for a client account    |
| *400*       | Invalid or missing input parameters                   |
| *403*       | Invalid session, please re-login to continue          |
| *429*       | Too many requests to the API                          |
| *500*       | Unexpected error                                      |
| *502*       | Not able to communicate with OMS                      |
| *503*       | Trade API service is unavailable                      |
| *504*       | Gateway timeout, trade API is unreachable             |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)  [[Back to README]](../README.md)
