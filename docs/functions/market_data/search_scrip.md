# **Scrip_Search**
Get the scrip details

```python
client.search_scrip(
    exchange_segment="",
    symbol="",
    expiry="",
    option_type="",
    strike_price="",
    ignore_50multiple=True,
)
```

> **Note:** Unlike most trading/portfolio methods, `search_scrip()` does not require a completed 2FA (TOTP) session — only `consumer_key` is required, since the underlying API authenticates via the `Authorization` header alone.

> **Note:** `exchange_segment` is mandatory but defaults to `""` — calling `search_scrip()` by keyword with only some of the other parameters (e.g. `search_scrip(expiry="", option_type="", strike_price="", ignore_50multiple=True)`, omitting `exchange_segment` entirely) returns a client-side validation error instead of raising `TypeError: missing 1 required positional argument`:
> ```json
> {
>     "error": [
>         {
>             "code": "10300",
>             "message": "Validation Errors! Exchange Segment is Mandate to proceed further"
>         }
>     ]
> }
> ```

> **Note:** The scrip-master CSV for the requested `exchange_segment` is cached on disk for the rest of the calendar day it was downloaded (TTL expires at midnight local time, default location `~/.kotak_neo/scrip_cache`, overridable via the `NEO_SCRIP_CACHE_DIR` environment variable). Repeat searches on the same day for the same segment reuse the cached file instead of re-downloading it.

### Example

```python
from neo_api_client import NeoAPI


# Only consumer_key is required — no totp_login/totp_validate needed
client = NeoAPI(environment="prod", consumer_key="your_consumer_key")

try:
    # get scrip search details for particular exchange segment
    client.search_scrip(
        exchange_segment="nse_cm", symbol="YESBANK", expiry="", option_type="", strike_price=""
    )

    # Futures contract: use option_type="FUT" (SDK-only alias for pOptionType == "XX")
    client.search_scrip(
        exchange_segment="nse_fo", symbol="NIFTY", expiry="", option_type="FUT", strike_price=""
    )
except Exception as e:
    print("Exception when calling scrip search api->scrip_search: %s\n" % e)
```
### Parameters

| Name                | Description                     | Type           |
|---------------------|---------------------------------|----------------|
| *exchange_segment*  | Mandatory. Unlike `place_order`/`margin_required`, generic aliases are resolved here: `nse_cm`/`NSE`/`nse`, `bse_cm`/`BSE`/`bse`, `nse_fo`/`NFO`/`nfo`, `bse_fo`/`BFO`/`bfo`, `mcx_fo`/`MCX`/`mcx`. Currency derivatives (`CDS`/`cds`/`cde_fo`) and BSE currency derivatives (`BCD`/`bcd`/`bcs-fo`) are not supported and return an error. | Str            |
| *symbol*            |                                 | Str            |
| *expiry*            | User can search multiple expiry - DDMMMYYYY, ex. 28JUN2023 | Str [optional] |
| *option_type*       | User can search option_type - `CE`/`PE`/`FUT` (comma-separated for multiple, e.g. `CE,PE`). `FUT` is an SDK-only alias for futures contracts — the scrip-master CSV marks these rows `XX` in `pOptionType` (not `CE`/`PE`), so the SDK maps `FUT` → `XX` internally before filtering. | Str [optional] |
| *strike_price*      | User can search strike_price - For ex. 45000, 40000-45000, >40000, <45000   | Str [optional] |
| *ignore_50multiple* | Whether to ignore strike prices that are not multiples of 50.               | bool [optional, default `True`] |


### Return type

**list**

### Sample response

```json

[
    {
        "pSymbol": 11915,
        "pGroup": "EQ",
        "pExchSeg": "nse_cm",
        "pInstType": null,
        "pSymbolName": "YESBANK",
        "pTrdSymbol": "YESBANK-EQ",
        "pOptionType": null,
        "pScripRefKey": "YESBANK",
        "pISIN": "INE528G01035",
        "pAssetCode": null,
        "pSubGroup": null,
        "pCombinedSymbol": null,
        "pDesc": "YES BANK LIMITED",
        "pAmcCode": null,
        "pContractId": null,
        "dTickSize": 1,
        "lLotSize": 1,
        "lExpiryDate": -1,
        "lMultiplier": -1,
        "lPrecision": 2,
        "dStrikePrice;": -1,
        "pExchange": "NSE",
        "pInstName": null,
        "pExpiryDate": null,
        "pIssueDate": 805593600.0,
        "pMaturityDate": null,
        "pListingDate": 805593600.0,
        "pNoDelStartDate": 0.0,
        "pNoDelEndDate": 0.0,
        "pBookClsStartDate": 1244246400.0,
        "pBookClsEndDate": 1244764800.0,
        "pRecordDate": 0.0,
        "pCreditRating": "16.65-20.35",
        "pReAdminDate": 0.0,
        "pExpulsionDate": 0.0,
        "pLocalUpdateTime": 1421948339.0,
        "pDeliveryUnits": null,
        "pPriceUnits": null,
        "pLastTradingDate": null,
        "pTenderPeridEndDate": null,
        "pTenderPeridStartDate": null,
        "pSellVarMargin": null,
        "pBuyVarMargin": null,
        "pInstrumentInfo": null,
        "pRemarksText": null,
        "pSegment": "CASH",
        "pNav": null,
        "pNavDate": null,
        "pMfAmt": null,
        "pSipSecurity": null,
        "pFaceValue": 200.0,
        "pTrdUnits": null,
        "pExerciseStartDate": null,
        "pExerciseEndDate": null,
        "pElmMargin": 0.0,
        "pVarMargin": 20.0,
        "pTotProposedLimitValue": null,
        "pScripBasePrice": null,
        "pSettlementType": "T+1",
        "pCurrectionTime": 315513000.0,
        "iPermittedToTrade": 0,
        "iBoardLotQty": 1,
        "iMaxOrderSize": 5392180,
        "iLotSize": 1,
        "dOpenInterest": 0,
        "dHighPriceRange": 2035.0,
        "dLowPriceRange": 1665.0,
        "dPriceNum": 1,
        "dGenDen": 1,
        "dGenNum": 1,
        "dPriceQuatation": 0,
        "dIssuerate": 0,
        "dPriceDen": 1,
        "dWarningQty": 0,
        "dIssueCapital": 31349900000.0,
        "dExposureMargin": 0,
        "dMinRedemptionQty": 0,
        "lFreezeQty": 5392180
    },
    {
        "pSymbol": 12900,
        "pGroup": "BL",
        "pExchSeg": "nse_cm",
        "pInstType": null,
        "pSymbolName": "YESBANK",
        "pTrdSymbol": "YESBANK-BL",
        "pOptionType": null,
        "pScripRefKey": "YESBANK-BL",
        "pISIN": "INE528G01035",
        "pAssetCode": null,
        "pSubGroup": null,
        "pCombinedSymbol": null,
        "pDesc": "YES BANK LIMITED",
        "pAmcCode": null,
        "pContractId": null,
        "dTickSize": 1,
        "lLotSize": 1,
        "lExpiryDate": -1,
        "lMultiplier": -1,
        "lPrecision": 2,
        "dStrikePrice;": -1,
        "pExchange": "NSE",
        "pInstName": null,
        "pExpiryDate": null,
        "pIssueDate": 816220800.0,
        "pMaturityDate": null,
        "pListingDate": 816220800.0,
        "pNoDelStartDate": 0.0,
        "pNoDelEndDate": 0.0,
        "pBookClsStartDate": 1244246400.0,
        "pBookClsEndDate": 1244764800.0,
        "pRecordDate": 0.0,
        "pCreditRating": "18.31-18.68",
        "pReAdminDate": 0.0,
        "pExpulsionDate": 0.0,
        "pLocalUpdateTime": 1421947175.0,
        "pDeliveryUnits": null,
        "pPriceUnits": null,
        "pLastTradingDate": null,
        "pTenderPeridEndDate": null,
        "pTenderPeridStartDate": null,
        "pSellVarMargin": null,
        "pBuyVarMargin": null,
        "pInstrumentInfo": null,
        "pRemarksText": null,
        "pSegment": "CASH",
        "pNav": null,
        "pNavDate": null,
        "pMfAmt": null,
        "pSipSecurity": null,
        "pFaceValue": 200.0,
        "pTrdUnits": null,
        "pExerciseStartDate": null,
        "pExerciseEndDate": null,
        "pElmMargin": null,
        "pVarMargin": null,
        "pTotProposedLimitValue": null,
        "pScripBasePrice": null,
        "pSettlementType": "T+1",
        "pCurrectionTime": 315513000.0,
        "iPermittedToTrade": 0,
        "iBoardLotQty": 1,
        "iMaxOrderSize": 0,
        "iLotSize": 1,
        "dOpenInterest": 0,
        "dHighPriceRange": 1868.0,
        "dLowPriceRange": 1831.0,
        "dPriceNum": 1,
        "dGenDen": 1,
        "dGenNum": 1,
        "dPriceQuatation": 0,
        "dIssuerate": 0,
        "dPriceDen": 1,
        "dWarningQty": 0,
        "dIssueCapital": 31349900000.0,
        "dExposureMargin": 0,
        "dMinRedemptionQty": 0,
        "lFreezeQty": 99999999
    }
]
```

### HTTP request headers

 - **Content-Type**: application/x-www-form-urlencoded

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
