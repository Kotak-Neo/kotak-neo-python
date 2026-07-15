# Place_Order
Place a New order

```python
client.place_order(
    exchange_segment="",
    product="",
    price="",
    order_type="",
    quantity="",
    validity="",
    trading_symbol="",
    transaction_type="",
    amo="NO",
    disclosed_quantity="0",
    pf="N",
    trigger_price="0",
    tag=None,
    scrip_token=None,
    square_off_type=None,
    stop_loss_type=None,
    stop_loss_value=None,
    square_off_value=None,
    last_traded_price=None,
    trailing_stop_loss=None,
    trailing_sl_value=None,
)
```

> **Note:** Market protection (`mp`) is always sent as `"0"` — it is not caller-configurable.

### Example


```python
from neo_api_client import NeoAPI


#First initialize session and generate session token
client = NeoAPI(environment='prod', access_token=None, neo_fin_key=None)
client.totp_login(mobilenumber="", ucc="", totp='')
client.totp_validate(mpin="")
try:
    # Place a Order
    client.place_order(
        exchange_segment="",
        product="",
        price="",
        order_type="",
        quantity="",
        validity="",
        trading_symbol="",
        transaction_type="",
        amo="NO",
        disclosed_quantity="0",
        pf="N",
        trigger_price="0",
        tag=None,
        scrip_token=None,
        square_off_type=None,
        stop_loss_type=None,
        stop_loss_value=None,
        square_off_value=None,
        last_traded_price=None,
        trailing_stop_loss=None,
        trailing_sl_value=None,
    )
except Exception as e:
    print("Exception when calling OrderApi->place_order: %s\n" % e)
```

### Parameters

| Name                 | Description                                                                                                                                                                                                                                                                                                                                                       | Type           |
|----------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------|
| *exchange_segment*   | nse_cm - NSE<br/>bse_cm - BSE<br/>nse_fo - NFO<br/>bse_fo - BFO<br/>cde_fo - CDS<br/>mcx_fo - MCX                                                                                                                                                                                                                                                               | Str            |
| *product*            | Allowed values: CNC, NRML, MIS, MTF (or their aliases, e.g. "Normal", "Cash and Carry")                                                                                                                                                                                                                           | Str            |
| *price*              | Mandatory. Zero or a positive value for MKT/SL-M orders; must be greater than zero for L/SL orders (a real limit price is required — price=0 is rejected client-side to prevent the exchange substituting a default price)                                                                                                                                                                                                                                                | Str            |
| *order_type*         | L - Limit<br/>MKT - Market<br/>SL - Stop loss limit<br/>SL-M - Stop loss market                                                                                                                                                                                                                                                                                   | Str            |
| *quantity*           | quantity of the order                                                                                                                                                                                                                                                                                                                                             | Str            |
| *validity*           | Allowed values: DAY, IOC. mcx_fo supports DAY only. GTC/EOS/GTD are not accepted.                                                                                                                                                                                                                                                                                  | Str            |
| *trading_symbol*     | pTrdSymbol in ScripMaster file                                                                                                                                                                                                                                                                                                                                    | Str            |
| *transaction_type*   | B(Buy), S(Sell)                                                                                                                                                                                                                                                                                                                                                   | Str            |
| *amo*                | YES/NO - (Default Value - NO)                                                                                                                                                                                                                                                                                                                                     | Str [optional] |
| *disclosed_quantity* | (Default Value - 0)                                                                                                                                                                                                                                                                                                                                               | Str [optional] |
| *pf*                 | Default Value - “N”                                                                                                                                                                                                                                                                                                                                               | Str [optional] |
| *trigger_price*      | Required for SL/SL-M stop-loss orders. Optional for L/MKT — if omitted (or passed as `None`), the SDK sends `"0"` to the API automatically, since the REST field is mandatory even though its value doesn't matter for those order types.                                                                                                                          | Str [optional] |
| *tag*                | Your own tag to track the order                                                                                                                                                                                                                                                                                                                                   | Str [optional] |
| *scrip_token*        | Applicable only for Bracket Order                                                                                                                                                                                                                                                                                                                                 | Str [optional] |
| *square_off_type*    | Applicable only for Bracket Order. Expected Values are 'Absolute' and 'Ticks'.                                                                                                                                                                                                                                                                                    | Str [optional] |
| *stop_loss_type*     | Applicable only for bracket Order. Expected Values are 'Absolute' and 'Ticks'.                                                                                                                                                                                                                                                                                    | Str [optional] |
| *stop_loss_value*    | Applicable only for Bracket Order                                                                                                                                                                                                                                                                                                                                 | Str [optional] |
| *square_off_value*   | Applicable only for Bracket Order                                                                                                                                                                                                                                                                                                                                 | Str [optional] |
| *last_traded_price*  | Applicable only for Bracket Order                                                                                                                                                                                                                                                                                                                                 | Str [optional] |
| *trailing_stop_loss* | Applicable only for Bracket Order. Expected Values are 'Y' and 'N'.                                                                                                                                                                                                                                                                                               | Str [optional] |
| *trailing_sl_value*  | Applicable only for Bracket Order. Expected Values are 'Y' and 'N'.                                                                                                                                                                                                                                                                                               | Str [optional] |


### Return type

**object**

### Sample response

```json
{
    "stat": "Ok",
    "nOrdNo": "",
    "stCode": 200
}

```
### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status Code | Description                                  |
|-------------|----------------------------------------------|
| *200*       | Order placed successfully                    |
| *400*       | Invalid or missing input parameters          |
| *403*       | Invalid session, please re-login to continue |
| *429*       | Too many requests to the API                 |
| *500*       | Unexpected error                             |
| *502*       | Not able to communicate with OMS             |
| *503*       | Trade API service is unavailable             |
| *504*       | Gateway timeout, trade API is unreachable    |


[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)  [[Back to README]](../README.md)
