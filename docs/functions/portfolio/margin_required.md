# **Margin_Required**
Get required margin details

```python
client.margin_required(
    exchange_segment="",
    price="",
    order_type="",
    product="",
    quantity="",
    instrument_token="",
    transaction_type="",
    broker_name="KOTAK",
    branch_id="ONLINE",
)
```

### Example

```python
from neo_api_client import NeoAPI


# First initialize session and generate session token
client = NeoAPI(environment="prod", access_token=None, neo_fin_key=None)
client.totp_login(mobilenumber="", ucc="", totp="")
client.totp_validate(mpin="")

try:
    client.margin_required(
        exchange_segment="nse_cm",
        price="100",
        order_type="L",
        product="CNC",
        quantity="1",
        instrument_token="11536",
        transaction_type="B",
    )
except Exception as e:
    print("Exception when calling margin_required->margin_required: %s\n" % e)
```

### Parameters

All parameters below are mandatory unless noted otherwise, and are validated client-side before the request is sent.

| Name               | Description                                                                | Type           |
|--------------------|-----------------------------------------------------------------------------|----------------|
| *exchange_segment* | Allowed values (exact match only, aliases are not accepted): `nse_cm`, `bse_cm`, `nse_fo`, `bse_fo`, `mcx_fo` | Str |
| *price*            | Zero or a positive value                                                    | Str            |
| *order_type*       | Allowed values (exact match only, aliases are not accepted): `L`, `MKT`, `SL`, `SL-M` | Str            |
| *product*          | Allowed values (exact match only, aliases are not accepted): `CNC`, `NRML`, `MIS`, `MTF` | Str |
| *quantity*         | Non-zero positive value                                                     | Str            |
| *instrument_token* | pSymbol in ScripMaster files. Must be a valid (positive integer) token      | Str            |
| *transaction_type* | Allowed values: `B` (Buy), `S` (Sell)                                       | Str            |
| *broker_name*      | Optional, defaults to "KOTAK". If provided, cannot be blank                 | Str            |
| *branch_id*        | Optional, defaults to "ONLINE". If provided, cannot be blank                | Str            |
| *stop_loss_type*   | Optional. The type of stop loss to use. Not validated client-side.          | Str            |
| *stop_loss_value*  | Optional. The value for the stop loss. Not validated client-side.           | Str            |
| *square_off_type*  | Optional. The type of square off to use. Not validated client-side.         | Str            |
| *square_off_value* | Optional. The value for the square off. Not validated client-side.          | Str            |
| *trailing_stop_loss* | Optional. The type of trailing stop loss to use. Not validated client-side. | Str          |
| *trailing_sl_value* | Optional. The value for the trailing stop loss. Not validated client-side.  | Str            |


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
