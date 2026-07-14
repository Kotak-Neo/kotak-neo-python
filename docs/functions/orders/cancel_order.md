# **Cancel_Order**
Cancel an order

```python
client.cancel_order(order_id = "")
```

> **Note:** Before sending the cancel request, the SDK always checks the order's current status on the order book. If the order is already `complete`, `traded`, `rejected`, or `cancelled`, the cancel is rejected client-side with a structured error (`status_code: 409`) instead of being sent to the exchange:
> ```json
> {
>     "status_code": 409,
>     "Error": "Order 230120000017243 is already 'complete' and can no longer be modified or cancelled.",
>     "ordSt": "complete",
>     "Reason": null,
>     "nOrdNo": "230120000017243"
> }
> ```
> If the order-book lookup itself fails (e.g. a transient network error), the SDK falls back to sending the cancel anyway rather than blocking on a lookup failure. `isVerify` is retained for backward compatibility but no longer changes this behavior, since the check is now always performed.

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
| *isVerify*  | Deprecated/no-op — kept for backward compatibility. The terminal-status check is now always performed regardless of this flag. | boolean   |
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
| *400*       | Invalid or missing input parameters          |
| *403*       | Invalid session, please re-login to continue |
| *409*       | Order is already complete/traded/rejected/cancelled — rejected client-side by the SDK, never sent to the exchange |
| *429*       | Too many requests to the API                 |
| *500*       | Unexpected error                             |
| *502*       | Not able to communicate with OMS             |
| *503*       | Trade API service is unavailable             |
| *504*       | Gateway timeout, trade API is unreachable    |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)  [[Back to README]](../README.md)
