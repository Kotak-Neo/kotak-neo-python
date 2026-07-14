# **Modify_Order**
Modify an existing order

## **Method 1 - Quick method**
```python
client.modify_order(instrument_token = "", exchange_segment = "", product = "", price = "", order_type = "", quantity= "",
                    validity = "", trading_symbol = "", transaction_type = "", order_id = "")
````

## **Method 2 - Delayed method**
Passing only `order_id` (no `instrument_token`/`exchange_segment`/`trading_symbol`) looks up the rest of the order's details from the order book.
```python
client.modify_order(order_id = "", price = "", quantity = "", trigger_price = "", validity = "", order_type = "", amo = "")
````

> **Note:** Before sending the modify request (either method), the SDK always checks the order's current status on the order book. If the order is already `complete`, `traded`, `rejected`, or `cancelled`, the modify is rejected client-side with a structured error (`status_code: 409`) instead of being sent to the exchange:
> ```json
> {
>     "status_code": 409,
>     "Error": "Order 220621000000097 is already 'rejected' and can no longer be modified or cancelled.",
>     "ordSt": "rejected",
>     "Reason": "Price is out of the current price range",
>     "nOrdNo": "220621000000097"
> }
> ```
> If the order-book lookup itself fails (e.g. a transient network error), the SDK falls back to sending the modify anyway rather than blocking on a lookup failure.

### Example


```python
from neo_api_client import NeoAPI
from neo_api_client import BaseUrl


#First initialize session and generate session token
client = NeoAPI(environment='prod', access_token=None, neo_fin_key=None)
client.totp_login(mobilenumber="", ucc="", totp='')
client.totp_validate(mpin="")

try:
    # Modify an existing order
    client.modify_order(instrument_token = "", exchange_segment = "", product = "", price = "",
                        order_type = "", quantity= "", validity = "", trading_symbol = "",transaction_type = "",
                        order_id = "", amo = "")

except Exception as e:
    print("Exception when calling OrderApi->modify_order: %s\n" % e)

```
### Parameters

| Name                 | Description                                                                                                              | Type           |
|----------------------|--------------------------------------------------------------------------------------------------------------------------|----------------|
| *instrument_token*   | pSymbol in ScripMaster file (first Column)                                                                               | Str [optional] |
| *exchange_segment*   | nse_cm - NSE<br/>bse_cm - BSE<br/>nse_fo - NFO<br/>bse_fo - BFO<br/>cde_fo - CDS<br/>mcx_fo - MCX                        | Str [optional] |
| *product*            | NRML - Normal<br/>CNC - Cash and Carry<br/>MIS - MIS<br/>INTRADAY - INTRADAY<br/>CO - Cover Order  | Str            |
| *price*              | Mandatory. Zero or a positive value for MKT/SL-M orders; must be greater than zero for L/SL orders (a real limit price is required — price=0 is rejected client-side to prevent the exchange substituting a default price)                                                                                    | Str            |
| *order_type*         | L - Limit<br/>MKT - Market<br/>SL - Stop loss limit<br/>SL-M - Stop loss market                                          | Str            |
| *quantity*           | quantity of the order                                                                                        | Str            |
| *validity*           | Allowed values: DAY, IOC. mcx_fo supports DAY only. GTC/EOS/GTD are not accepted.                                                                                                                                                                                                                                                                                  | Str            |
| *trading_symbol*     | pTrdSymbol in ScripMaster file                                                                                          | Str            |
| *transaction_type*   | B(Buy), S(sell)                                                                                                          | Str            |
| *order_id*           | order id of the order you want to modify                                                                                       | Str            |
| *amo*                | YES/NO - (Default Value - NO)                                                                         | Str [optional] |
| *market_protection*  | String - (Default Value - 0)                                                                                             | Str [optional] |
| *dd*                 | Default Value - “NA”                                                                                                     | Str [optional] |
| *filled_quantity*    | (Default Value - 0)                                                                                                      | Str [optional] |
| *trigger_price*      | Required for SL/SL-M stop-loss orders. Optional for L/MKT — if omitted (or passed as `None`), the SDK sends `"0"` to the API automatically, since the REST field is mandatory even though its value doesn't matter for those order types. When modifying via `order_id` only, an existing order's trigger price is preserved unless you're changing to L/MKT.                                                          | Str [optional] |

### Return type

**object**

### Sample response

```json
{
    "stat": "Ok",
    "nOrdNo": "220621000000097",
    "stCode": 200
}

```

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details
| Status Code | Description                                  |
|-------------|----------------------------------------------|
| *200*       | Order modified successfully                  |
| *400*       | Invalid or missing input parameters          |
| *403*       | Invalid session, please re-login to continue |
| *409*       | Order is already complete/traded/rejected/cancelled — rejected client-side by the SDK, never sent to the exchange |
| *429*       | Too many requests to the API                 |
| *500*       | Unexpected error                             |
| *502*       | Not able to communicate with OMS             |
| *503*       | Trade API service is unavailable             |
| *504*       | Gateway timeout, trade API is unreachable    |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)  [[Back to README]](../README.md)
