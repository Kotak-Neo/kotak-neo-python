# **Modify_Order**
Modify an existing order

```python
client.modify_order(order_id = "", price = "", order_type = "", quantity= "", validity = "", product = "")
````

> **Note:** The modify request is always sent straight to the backend — the exchange is the source of truth on whether an order (e.g. one that's already `complete`/`traded`/`rejected`/`cancelled`) can still be modified. The SDK does not pre-check the order book or fill in missing fields from it before sending.
>
> If the order is already complete, the backend rejects the modify with `{"stCode": 1021, "errMsg": "order is completed", ...}`. The SDK annotates this response with `status_code: 409` so you can detect it without depending on the backend's internal `stCode`:
> ```json
> {
>     "stCode": 1021,
>     "errMsg": "order is completed",
>     "stat": "please provide valid order number",
>     "status_code": 409
> }
> ```
>
> Market protection (`mp`) is always sent as `"0"` — it is not caller-configurable.

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
    client.modify_order(order_id = "", price = "", order_type = "", quantity= "", validity = "",
                        product = "", amo = "")

except Exception as e:
    print("Exception when calling OrderApi->modify_order: %s\n" % e)

```
### Parameters

| Name                 | Description                                                                                                              | Type           |
|----------------------|--------------------------------------------------------------------------------------------------------------------------|----------------|
| *order_id*           | order id of the order you want to modify                                                                                       | Str            |
| *price*              | Mandatory. Zero or a positive value for MKT/SL-M orders; must be greater than zero for L/SL orders (a real limit price is required — price=0 is rejected client-side to prevent the exchange substituting a default price)                                                                                    | Str            |
| *order_type*         | L - Limit<br/>MKT - Market<br/>SL - Stop loss limit<br/>SL-M - Stop loss market                                          | Str            |
| *quantity*           | quantity of the order                                                                                        | Str            |
| *validity*           | Allowed values: DAY, IOC. GTC/EOS/GTD are not accepted.                                                                                                                                                                                                                                                                                  | Str            |
| *product*            | Allowed values (exact match only, aliases are not accepted): CNC, NRML, MIS, MTF | Str [optional] |
| *amo*                | YES/NO - (Default Value - NO)                                                                         | Str [optional] |
| *dd*                 | Default Value - “NA”                                                                                                     | Str [optional] |
| *filled_quantity*    | (Default Value - 0)                                                                                                      | Str [optional] |
| *trigger_price*      | Required for SL/SL-M stop-loss orders. Optional for L/MKT — if omitted (or passed as `None`), the SDK sends `"0"` to the API automatically, since the REST field is mandatory even though its value doesn't matter for those order types.                                                          | Str [optional] |

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
| *409*       | Order is already complete — SDK-added `status_code` on the backend's `stCode: 1021` rejection |
| *429*       | Too many requests to the API                 |
| *500*       | Unexpected error                             |
| *502*       | Not able to communicate with OMS             |
| *503*       | Trade API service is unavailable             |
| *504*       | Gateway timeout, trade API is unreachable    |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)  [[Back to README]](../README.md)
