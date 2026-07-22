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
    trigger_price="0",
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
        trigger_price="0",
    )
except Exception as e:
    print("Exception when calling OrderApi->place_order: %s\n" % e)
```

### Parameters

| Name                 | Description                                                                                                                                                                                                                                                                                                                                                       | Type           |
|----------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------|
| *exchange_segment*   | Allowed values (exact match only — no aliases accepted): `nse_cm`, `bse_cm`, `nse_fo`, `bse_fo`, `mcx_fo`. Generic aliases like `NSE`/`BSE`/`NFO`/`BFO`/`MCX` are rejected (they're ambiguous about which specific segment, e.g. cash vs. F&O, the order applies to). Currency derivatives (`CDS`/`cds`/`cde_fo`) and BSE currency derivatives (`BCD`/`bcd`/`bcs-fo`) are not accepted at all — not a supported segment.                                                                                                                                                                                                                                                               | Str            |
| *product*            | Allowed values (exact match only, aliases are not accepted): CNC, NRML, MIS, MTF                                                                                                                                                                                                                           | Str            |
| *price*              | Mandatory. Zero or a positive value for MKT/SL-M orders; must be greater than zero for L/SL orders (a real limit price is required — price=0 is rejected client-side to prevent the exchange substituting a default price)                                                                                                                                                                                                                                                | Str            |
| *order_type*         | Allowed values (exact match only — no aliases accepted): `L` (Limit), `MKT` (Market), `SL` (Stop loss limit), `SL-M` (Stop loss market). Aliases like `Limit`/`Market`/`Stop loss limit`/`Stop loss market` (and multi-leg types `SP`/`2L`/`3L`) are rejected.                                                                                                                                                                                                                                                                                  | Str            |
| *quantity*           | quantity of the order                                                                                                                                                                                                                                                                                                                                             | Str            |
| *validity*           | Allowed values: DAY, IOC. mcx_fo supports DAY only. GTC/EOS/GTD are not accepted.                                                                                                                                                                                                                                                                                  | Str            |
| *trading_symbol*     | pTrdSymbol in ScripMaster file                                                                                                                                                                                                                                                                                                                                    | Str            |
| *transaction_type*   | B(Buy), S(Sell)                                                                                                                                                                                                                                                                                                                                                   | Str            |
| *amo*                | YES/NO - (Default Value - NO)                                                                                                                                                                                                                                                                                                                                     | Str [optional] |
| *disclosed_quantity* | (Default Value - 0)                                                                                                                                                                                                                                                                                                                                               | Str [optional] |
| *trigger_price*      | Required for SL/SL-M stop-loss orders. Optional for L/MKT — if omitted (or passed as `None`), the SDK sends `"0"` to the API automatically, since the REST field is mandatory even though its value doesn't matter for those order types.                                                                                                                          | Str [optional] |


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
