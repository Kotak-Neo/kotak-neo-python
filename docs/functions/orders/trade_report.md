# **Trade_Report**

Get all traded order details
```python
client.trade_report()
```

> **Note:** Fetching the trade report filtered by a single order ID is not
> supported server-side — `trade_report()` always returns the full list of
> trades for the day; filter the `data` list client-side on `nOrdNo` (the
> Nest order ID, shown in the sample response below) to reconcile fills for
> one specific order.
>
> [`order_report(order_id=...)`](./order_report.md) is **not** a substitute
> for this: it returns that order's current *status* from
> `/quick/user/orders/<order_id>` (e.g. pending/complete/rejected), not its
> executed *fills* (price, quantity, fill time, exchange order ID, etc.).
> Order status and fill-level trade data are different concerns — use
> `order_report()` to check where an order stands, and this endpoint
> (filtered client-side as above) to reconcile what actually executed.

### Example

```python
from neo_api_client import NeoAPI


# First initialize session and generate session token
client = NeoAPI(environment="prod", access_token=None, neo_fin_key=None)
client.totp_login(mobilenumber="", ucc="", totp="")
client.totp_validate(mpin="")

try:
    # Get all trade details
    client.trade_report()
except Exception as e:
    print("Exception when trade report API->trade_report: %s\n" % e)
```

### Parameters

None

### Return type

**object**

### Sample response

```json
{
    "stat": "ok",
    "stCode": 200,
    "data": [
        {
            "actId": "",
            "algCat": "NA",
            "algId": "NA",
            "avgPrc": "9.39",
            "boeSec": 1737536296,
            "brdLtQty": 1,
            "brkClnt": "NA",
            "cstFrm": "C",
            "exOrdId": "1100000059569867",
            "exp": "-",
            "expDt": "NA",
            "exSeg": "nse_cm",
            "exTm": "22-Jan-2025 14:28:01",
            "fldQty": 1,
            "flDt": "22-Jan-2025",
            "flId": "207983744",
            "flLeg": 1,
            "flTm": "14:28:16",
            "minQty": 0,
            "nOrdNo": "250122000612876",
            "nReqId": "1",
            "optTp": "- ",
            "ordDur": "NA",
            "ordGenTp": "--",
            "prcTp": "L",
            "prod": "NRML",
            "rmk": "--",
            "rptTp": "fill",
            "series": "EQ",
            "stkPrc": "0.00",
            "sym": "IDEA",
            "trdSym": "IDEA-EQ",
            "trnsTp": "B",
            "usrId": "AVRPC7535J",
            "genDen": "1",
            "genNum": "1",
            "hsUpTm": "2025/01/22 14:28:16",
            "GuiOrdId": "",
            "locId": "111111111111100",
            "lotSz": "1",
            "multiplier": "1",
            "ordSrc": "NA",
            "prcNum": "1",
            "prcDen": "1",
            "strategyCode": "",
            "precision": "2",
            "tok": "",
            "updRecvTm": 1737536296355319176,
            "uSec": "1737536296",
            "posFlg": "",
            "prc": "",
            "qty": 0,
            "tm": "",
            "it": "EQ"
        },
        {
            "actId": "",
            "algCat": "NA",
            "algId": "NA",
            "avgPrc": "9.39",
            "boeSec": 1737536581,
            "brdLtQty": 1,
            "brkClnt": "NA",
            "cstFrm": "C",
            "exOrdId": "1100000060414692",
            "exp": "-",
            "expDt": "NA",
            "exSeg": "nse_cm",
            "exTm": "22-Jan-2025 14:32:53",
            "fldQty": 1,
            "flDt": "22-Jan-2025",
            "flId": "208109719",
            "flLeg": 1,
            "flTm": "14:33:01",
            "minQty": 0,
            "nOrdNo": "250122000624384",
            "nReqId": "1",
            "optTp": "- ",
            "ordDur": "NA",
            "ordGenTp": "--",
            "prcTp": "L",
            "prod": "NRML",
            "rmk": "--",
            "rptTp": "fill",
            "series": "EQ",
            "stkPrc": "0.00",
            "sym": "IDEA",
            "trdSym": "IDEA-EQ",
            "trnsTp": "B",
            "usrId": "AVRPC7535J",
            "genDen": "1",
            "genNum": "1",
            "hsUpTm": "2025/01/22 14:33:01",
            "GuiOrdId": "",
            "locId": "111111111111100",
            "lotSz": "1",
            "multiplier": "1",
            "ordSrc": "NA",
            "prcNum": "1",
            "prcDen": "1",
            "strategyCode": "",
            "precision": "2",
            "tok": "",
            "updRecvTm": 1737536581846260853,
            "uSec": "1737536581",
            "posFlg": "",
            "prc": "",
            "qty": 0,
            "tm": "",
            "it": "EQ"
        }
    ]
}
```

### HTTP request headers

 - **Accept**: application/json

### HTTP response details
| Status Code | Description                                  |
|-------------|----------------------------------------------|
| *200*       | ok                                           |
| *400*       | Invalid or missing input parameters          |
| *403*       | Invalid session, please re-login to continue |
| *429*       | Too many requests to the API                 |
| *500*       | Unexpected error                             |
| *502*       | Not able to communicate with OMS             |
| *503*       | Trade API service is unavailable             |
| *504*       | Gateway timeout, trade API is unreachable    |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)  [[Back to README]](../README.md)
