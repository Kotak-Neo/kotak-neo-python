# **Limits**
Get RMS Limits details of your demat account

```python
client.limits()
```

### Example

```python
from neo_api_client import NeoAPI


#First initialize session and generate session token
client = NeoAPI(environment='prod', access_token=None, neo_fin_key=None)
client.totp_login(mobilenumber="", ucc="", totp='')
client.totp_validate(mpin="")

try:
    client.limits(segment="ALL", exchange="ALL",product="ALL")
except Exception as e:
    print("Exception when calling Limits->limits: %s\n" % e)
```

### Parameters
| Name        | Description                                 | Type           |
|-------------|---------------------------------------------|----------------|
| *segment*   | CASH, FO, ALL (Default value - ALL)         | str [Optional] |
| *exchange*  | NSE, BSE, ALL (Default value - ALL)         | str [Optional] |
| *product*   | CNC, NRML, MIS, ALL (Default value - ALL)   | str [Optional] |


### Return type

**object**

### Sample response

```json
{
    "Category": "CLIENT_SPECIAL",
    "EntityId": "",
    "BoardLotLimit": "5000",
    "CollateralValue": "38.19",
    "Collateral": "0",
    "RmsCollateral": "0",
    "AdhocMargin": "0",
    "NotionalCash": "0",
    "CdsSpreadBenefit": "0",
    "AmountUtilizedPrsnt": "0",
    "UnrealizedMtomPrsnt": "0",
    "RealizedMtomPrsnt": "0",
    "ExposureMarginPrsnt": "0",
    "SpanMarginPrsnt": "0",
    "NfospreadBenefit": "0",
    "PremiumPrsnt": "0",
    "MarginVarPrsnt": "0",
    "MarginScripBasketPrsnt": "18.78",
    "MtomWarningPrcntPrsnt": "0",
    "MarginWarningPrcntPrsnt": "49.175177",
    "MtomSquareOffWarningPrcntPrsnt": "0",
    "MarginUsed": "18.78",
    "RmsPayInAmt": "0",
    "RmsPayOutAmt": "0",
    "Net": "19.409999999999997",
    "SpecialMarginPrsnt": "0",
    "DaneLimit": "0",
    "DeliveryMarginPresent": "0",
    "CncSellcrdPresent": "0",
    "CollateralValueMult": "1",
    "AdhocLimitMult": "1",
    "RmsCollateralMult": "1",
    "NationalCashMult": "1",
    "ComSpanMrgnNrmlPrsnt": "0",
    "ComSpanMrgnMisPrsnt": "0",
    "ComExpsrMrgnNrmlPrsnt": "0",
    "ComExpsrMrgnMisPrsnt": "0",
    "AddMrgnNrmlPrsnt": "0",
    "AddMrgnMisPrsnt": "0",
    "AddPreExpMrgnNrmlPrsnt": "0",
    "AddPreExpMrgnMisPrsnt": "0",
    "SplMrgnNrmlPrsnt": "0",
    "SplMrgnMisPrsnt": "0",
    "TenderMrgnNrmlPrsnt": "0",
    "TenderMrgnMisPrsnt": "0",
    "DeliveryMrgnNrmlPrsnt": "0",
    "DeliveryMrgnMisPrsnt": "0",
    "CurExpMrgnNrmlPrsnt": "0",
    "CurExpMrgnMisPrsnt": "0",
    "CurPremiumNrmlPrsnt": "0",
    "CurPremiumMisPrsnt": "0",
    "CurSpanMrgnNrmlPrsnt": "0",
    "CurSpanMrgnMisPrsnt": "0",
    "FoPremiumNrmlPrsnt": "0",
    "FoPremiumMisPrsnt": "0",
    "FoExpMrgnNrmlPrsnt": "0",
    "FoExpMrgnMisPrsnt": "0",
    "FoSpanrgnNrmlPrsnt": "0",
    "FoSpanrgnMisPrsnt": "0",
    "MrgnScrpBsktNrmlPrsnt": "18.78",
    "MrgnScrpBsktMisPrsnt": "0",
    "MrgnScrpBsktCncPrsnt": "0",
    "MrgnVarNrmlPrsnt": "0",
    "MrgnVarMisPrsnt": "0",
    "AmtUntilizedPrsnt": "0",
    "CncMrgnVarPrsnt": "0",
    "MarginUsedPrsnt": "18.78",
    "CashUnRlsMtomPrsnt": "-0.24",
    "FoUnRlsMtomPrsnt": "0",
    "ComUnRlsMtomPrsnt": "0",
    "CurUnRlsMtomPrsnt": "0",
    "CashRlsMtomPrsnt": "0",
    "FoRlsMtomPrsnt": "0",
    "ComRlsMtomPrsnt": "0",
    "CurRlsMtomPrsnt": "0",
    "BrokeragePrsnt": "0",
    "SlbmLimit": "0",
    "SlbmVarElm": "",
    "SlbmMtom": "",
    "LendingFee": "",
    "RmsMutualFundAmt": "0",
    "TimeStamp": "1737540175823",
    "AuxRmsCollateral": "0",
    "AuxNotionalCash": "0",
    "AuxAdhocMargin": "0",
    "stCode": 200,
    "stat": "Ok",
    "RmsIpoAmt": "0"
}
```

### HTTP request headers

 - **Accept**: application/json

### HTTP response details
| Status Code | Description                                  |
|-------------|----------------------------------------------|
| *200*       | Gets the Limits data for a client account    |
| *400*       | Invalid or missing input parameters          |
| *403*       | Invalid session, please re-login to continue |
| *429*       | Too many requests to the API                 |
| *500*       | Unexpected error                             |
| *502*       | Not able to communicate with OMS             |
| *503*       | Trade API service is unavailable             |
| *504*       | Gateway timeout, trade API is unreachable    |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)  [[Back to README]](../README.md)
