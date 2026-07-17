# **Cancel_Order**
Cancel an order

```python
client.cancel_order(order_id = "")
```

> **Note:** The cancel request is always sent straight to the backend — the exchange is the source of truth on whether an order (e.g. one that's already `complete`/`traded`/`rejected`/`cancelled`) can still be cancelled. The SDK does not pre-check the order book before sending. `isVerify` is retained for backward compatibility but has no effect on this behavior.
>
> If the order is already complete, the backend rejects the cancel with `{"stCode": 1021, "errMsg": "order is completed", ...}`. The SDK annotates this response with `status_code: 400` so you can detect it without depending on the backend's internal `stCode`:
> ```json
> {
>     "stCode": 1021,
>     "errMsg": "order is completed",
>     "stat": "please provide valid order number",
>     "status_code": 400
> }
> ```

### Example


```python
from neo_api_client import NeoAPI


#First initialize session and generate session token
client = NeoAPI(environment='prod', access_token=None, neo_fin_key=None)
client.totp_login(mobilenumber="", ucc="", totp='')
client.totp_validate(mpin="")

try:
    # Cancel an order
    client.cancel_order(order_id = "")
except Exception as e:
    print("Exception when calling OrderApi->cancel_order: %s\n" % e)
```

### Parameters
| Name        | Description         | Type      |
|-------------|---------------------|-----------|
| *order_id*  | Order ID to cancel | str       |
| *isVerify*  | Deprecated/no-op — kept for backward compatibility only. | boolean   |
| *amo*       | After market order - YES, NO (optional, Default Value - NO) | str   |

### Return type

**object**

### Sample response

```json
{
    "stat": "Ok",
    "nOrdNo": "230120000017243",
    "stCode": 200
}
```

### HTTP request headers

 - **Accept**: application/json

### HTTP response details
| Status Code | Description                                  |
|-------------|----------------------------------------------|
| *200*       | Order cancelled successfully                 |
| *400*       | Invalid or missing input parameters, or the order is already complete — SDK-added `status_code` on the backend's `stCode: 1021` rejection |
| *403*       | Invalid session, please re-login to continue |
| *429*       | Too many requests to the API                 |
| *500*       | Unexpected error                             |
| *502*       | Not able to communicate with OMS             |
| *503*       | Trade API service is unavailable             |
| *504*       | Gateway timeout, trade API is unreachable    |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)  [[Back to README]](../README.md)
