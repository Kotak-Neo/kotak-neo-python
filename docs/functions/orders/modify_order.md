# **Modify_Order**
Modify an existing order

## **Method 1 - Quick method**
```python
client.modify_order(instrument_token = "", exchange_segment = "", product = "", price = "", order_type = "", quantity= "",
                    validity = "", trading_symbol = "", transaction_type = "", order_id = "")
````

## **Method 2 - Delayed method**
This method verifies the order status first and then modifies the order if it is open.
```python
client.modify_order(order_id = "", price = "", quantity = "", trigger_price = "", validity = "", order_type = "", amo = "")
````

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
| *price*              | price of the order                                                                                    | Str [optional] |
| *order_type*         | L - Limit<br/>MKT - Market<br/>SL - Stop loss limit<br/>SL-M - Stop loss market                                          | Str            |
| *quantity*           | quantity of the order                                                                                        | Str            |
| *validity*           | Validity of the order <br/> DAY - (Applicable for all orders across all segments)<br/> IOC - Immediate or Cancel (Not applicable for CO)<br/> GTC - Good Till Cancel (Applicable only for orders in MCX market)<br/> EOS - End of Session (Applicable only for orders in BSE and MCX market)<br/> GTD - Good Till Date (Applicable only for orders in MCX market) | Str [optional] |
| *trading_symbol*     | pTrdSymbol in ScripMaster file                                                                                          | Str            |
| *transaction_type*   | B(Buy), S(sell)                                                                                                          | Str            |
| *order_id*           | order id of the order you want to modify                                                                                       | Str            |
| *amo*                | YES/NO - (Default Value - NO)                                                                         | Str [optional] |
| *market_protection*  | String - (Default Value - 0)                                                                                             | Str [optional] |
| *dd*                 | Default Value - “NA”                                                                                                     | Str [optional] |
| *filled_quantity*    | (Default Value - 0)                                                                                                      | Str [optional] |
| *trigger_price*      | Optional, required for stop loss and cover order                                                          | Str [optional] |

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
| *429*       | Too many requests to the API                 |
| *500*       | Unexpected error                             |
| *502*       | Not able to communicate with OMS             |
| *503*       | Trade API service is unavailable             |
| *504*       | Gateway timeout, trade API is unreachable    |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)  [[Back to README]](../README.md)
