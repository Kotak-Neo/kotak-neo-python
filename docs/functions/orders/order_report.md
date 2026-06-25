# **Order_Report**

Get all order details<br/>
```python
client.order_report()
```

### Example

```python
from neo_api_client import NeoAPI


#First initialize session and generate session token
client = NeoAPI(environment='prod', access_token=None, neo_fin_key=None)
client.totp_login(mobilenumber="", ucc="", totp='')
client.totp_validate(mpin="")

try:
    # Get all order details
    client.order_report()
except Exception as e:
    print("Exception when order report API->order_report: %s\n" % e)
```

### Return type

**object**

### Sample response

```json
{
    "stat": "Ok",
    "data": [
        {
            "actId": "",
            "algId": "NA",
            "algCat": "NA",
            "algSeqNo": "NA",
            "avgPrc": "0.00",
            "brdLtQty": "1",
            "brkClnt": "08081",
            "cnlQty": 0,
            "coPct": 0,
            "defMktProV": "0",
            "dscQtyPct": "0",
            "dscQty": 0,
            "exUsrInfo": "NA",
            "exCfmTm": "22-Jan-2025 14:28:01",
            "exOrdId": "1100000059569867",
            "expDt": "NA",
            "expDtSsb": "-",
            "exSeg": "nse_cm",
            "fldQty": 0,
            "boeSec": 1737536281,
            "mktProPct": "--",
            "mktPro": "0",
            "mfdBy": "NA",
            "minQty": 0,
            "mktProFlg": "0",
            "noMktProFlg": "0",
            "nOrdNo": "250122000612876",
            "optTp": "- ",
            "ordAutSt": "NA",
            "odCrt": "NA",
            "ordDtTm": "22-Jan-2025 14:28:01",
            "ordEntTm": "22-Jan-2025 14:28:01",
            "ordGenTp": "NA",
            "ordSrc": "",
            "ordValDt": "NA",
            "prod": "NRML",
            "prc": "9.39",
            "prcTp": "L",
            "qty": 1,
            "refLmtPrc": 0,
            "rejRsn": "--",
            "rmk": "--",
            "rptTp": "NA",
            "reqId": "1",
            "series": "EQ",
            "sipInd": "NA",
            "stat": "open",
            "ordSt": "open",
            "stkPrc": "0.00",
            "sym": "IDEA",
            "symOrdId": "NA",
            "tckSz": "0.0100",
            "tok": "14366",
            "trnsTp": "B",
            "trgPrc": "0.00",
            "trdSym": "IDEA-EQ",
            "unFldSz": 1,
            "usrId": "",
            "uSec": "1737536281",
            "vldt": "DAY",
            "classification": "0",
            "vendorCode": "",
            "genDen": "1",
            "genNum": "1",
            "prcNum": "1",
            "prcDen": "1",
            "lotSz": "1",
            "multiplier": "1",
            "precision": "2",
            "hsUpTm": "2025/01/22 14:28:01",
            "GuiOrdId": "",
            "locId": "111111111111100",
            "appInstlId": "NA",
            "ordModNo": "",
            "strategyCode": "NA",
            "updRecvTm": 1737536281933015920,
            "it": "EQ"
        }
    ],
    "stCode": 200
}
```

### HTTP request headers

 - **Accept**: application/json

### HTTP response details
| Status Code | Description                                  |
|-------------|----------------------------------------------|
| *200*       | Order report retrieved successfully          |
| *400*       | Invalid or missing input parameters          |
| *403*       | Invalid session, please re-login to continue |
| *429*       | Too many requests to the API                 |
| *500*       | Unexpected error                             |
| *502*       | Not able to communicate with OMS             |
| *503*       | Trade API service is unavailable             |
| *504*       | Gateway timeout, trade API is unreachable    |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)  [[Back to README]](../README.md)
