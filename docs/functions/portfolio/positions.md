# **Positions**
Gets positions

```python
client.positions()
```

### Example

```python
from neo_api_client import NeoAPI


# First initialize session and generate session token
client = NeoAPI(environment="prod", access_token=None, neo_fin_key=None)
client.totp_login(mobilenumber="", ucc="", totp="")
client.totp_validate(mpin="")

try:
    client.positions()
except Exception as e:
    print("Exception when calling PositionsApi->positions: %s\n" % e)
```

### Return type

**object**

### Sample response
```json
{
    "stat": "ok",
    "stCode": 200,
    "data": [
        {
            "actId": "ABCXYZ61",
            "brdLtQty": 225,
            "cfBuyAmt": "0.00",
            "cfSellAmt": "0.00",
            "cfBuyQty": "0",
            "cfSellQty": "0",
            "exSeg": "nse_fo",
            "buyAmt": "475200.00",
            "sellAmt": "0.00",
            "flBuyQty": "225",
            "flSellQty": "0",
            "prod": "NRML",
            "series": "XX",
            "tok": "61304",
            "trdSym": "TCS26JULFUT",
            "optTp": "XX",
            "stkPrc": "0.00",
            "type": "FUTSTK",
            "sym": "TCS",
            "sqrFlg": "Y",
            "posFlg": "true",
            "lotSz": "225",
            "multiplier": "1",
            "precision": "2",
            "prcNum": "1",
            "prcDen": "1",
            "hsUpTm": "2026/07/24 12:57:46",
            "expDt": "28 Jul, 2026",
            "exp": "1785196800",
            "genNum": "1",
            "genDen": "1",
            "dscQty": "",
            "upldPrc": "0.00",
            "updRecvTm": 1784878066658915084
        }
    ]
}

```

### Positions Calculations
#### Quantity Fields
1. Total Buy Qty = (`cfBuyQty` + `flBuyQty`)
2. Total Sell qty = (`cfSellQty` + `flSellQty`)
3. Carry Fwd Qty = (`cfBuyQty` - `cfSellQty`)
4. Net qty = Total Buy Qty - Total Sell qty </br>
For FnO Scrips, divide all the parameters from Positions API response(`cfBuyQty`, `flBuyQty`, `cfSellQty`, `flSellQty`)  by `lotSz`

#### Amount Fields
1. Total Buy Amt = (`cfBuyAmt` + `buyAmt`)
2. Total Sell Amt = (`cfSellAmt` + `sellAmt`)

#### Avg Price Fields
1. Buy Avg Price = <sup>Total Buy Amt</sup>/<sub>(Total Buy Qty * `multiplier` * (`genNum`/`genDen`) * (`prcNum`/ `prcDen`))</sub>

2. Sell Avg Price = <sup>Total Sell Amt</sup>/<sub>(Total Sell qty * `multiplier` * (`genNum`/ `genDen`) * (`prcNum`/ `prcDen`))</sub>
3. Avg Price </br>
    a. If Total Buy Qty > Total Sell qty, then Buy Avg Price </br>
    b. If Total Buy Qty < Total Sell qty, then Sell Avg Price </br>
    c. If Total Buy Qty = Total Sell qty, then 0 </br>
You need to calculate the average price to a specific number of decimal places that is decided by `precision` field.

#### Profit N Loss

PnL = (Total Sell Amt - Total Buy Amt) + (Net qty * LTP *  `multiplier` * (<sup>`genNum`</sup>/<sub>`genDen`</sub>) * (<sup>`prcNum`</sup>/<sub>`prcDen`</sub>) )


### HTTP request headers

 - **Accept**: application/json


### HTTP response details
| Status Code | Description                                  |
|-------------|----------------------------------------------|
| *200*       | Gets the Positoin data for a client account  |
| *400*       | Invalid or missing input parameters          |
| *403*       | Invalid session, please re-login to continue |
| *429*       | Too many requests to the API                 |
| *500*       | Unexpected error                             |
| *502*       | Not able to communicate with OMS             |
| *503*       | Trade API service is unavailable             |
| *504*       | Gateway timeout, trade API is unreachable    |
