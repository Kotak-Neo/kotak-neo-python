# Option Chain

Get the option chain (calls/puts) or futures chain for an underlying, with
per-strike quote and open-interest data.

## Function Signature

```python
client.option_chain(exchange, underlying, expiry=None, instrument_type=None, count=None)
```

> **Note:** Like `quotes()`/[`expiries()`](./expiries.md), this does not require
> a completed 2FA (TOTP) session — only `consumer_key` is required.

### Example

```python
from neo_api_client import NeoAPI

# Only consumer_key is required — no totp_login/totp_validate needed
client = NeoAPI(consumer_key="your-token-from-neo-app", environment="prod")

try:
    response = client.option_chain(
        exchange="nse_fo",
        underlying="RELIANCE",
        expiry="2026-06-23",
        instrument_type="option",
        count=40,
    )
    print(response)
except Exception as e:
    print("Exception when calling option_chain: %s\n" % e)
```

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `exchange` | str | Yes | Exchange segment. One of `nse_fo`, `bse_fo`, `mcx_fo`. |
| `underlying` | str | Yes | Underlying name, e.g. `RELIANCE`, `NIFTY`. Matches `pSymbolName` in the scrip master file. |
| `expiry` | str | No | ISO expiry date (`YYYY-MM-DD`), from [`expiries()`](./expiries.md). Defaults to the nearest expiry if omitted. |
| `instrument_type` | str | No | `option` (default) or `fut`. |
| `count` | int | No | Number of strikes. Default 40 (80 instruments: 40 calls + 40 puts). |

Passing `instrument_type="fut"` with `expiry=None` returns every available
futures contract in the `fut[]` array; passing a specific `expiry` returns
only that one contract.

## Return Type

**dict**

## Sample Response — Option chain

```json
{
  "data": {
    "common_data": {
      "mktLot": "65",
      "multiplier": "1",
      "unlSymbol": "NIFTY",
      "exSeg": "nse_fo",
      "expiryDt": "2026-06-23"
    },
    "call": [
      {
        "instrument": {
          "neoSymbol": "nse_fo|71472",
          "symbol": "NIFTY26JUN22250CE",
          "optionType": "CE",
          "strikePrice": "22250",
          "moneyness": "ATM"
        },
        "quote": {
          "ltp": "166.7500",
          "open": "89.8000",
          "high": "214.0000",
          "low": "77.1000",
          "prevClose": "99.7000",
          "close": null,
          "volume": 225431505
        },
        "openInterest": {
          "current": 10715645,
          "previous": 13647630,
          "change": -2931985,
          "changePct": -21.48
        }
      }
    ],
    "put": []
  }
}
```

`openInterest.change`/`changePct` are server-computed from current vs.
previous OI, so every caller gets a consistent value. `close` stays `null`
intraday and is populated at settlement; `prevClose` is stable for the
session, so day-change needs no time-of-day logic.

## Sample Response — Futures chain (`instrument_type="fut"`)

```json
{
  "data": {
    "common_data": {
      "mktLot": "65",
      "multiplier": "1",
      "unlSymbol": "NIFTY",
      "exSeg": "nse_fo",
      "expiryDt": null
    },
    "call": [],
    "put": [],
    "fut": [
      {
        "inst": {
          "neoSymbol": "nse_fo|53001",
          "symbol": "NIFTY26JULFUT",
          "expiryDt": "31-JUL-2026"
        },
        "quote": {
          "ltp": "24485.20",
          "o": "24455.00",
          "h": "24512.00",
          "l": "24428.00",
          "c": "24485.20",
          "pc": "24322.10",
          "vol": "9852340"
        },
        "oi": {
          "cur": "13930930",
          "prev": "13801200",
          "chg": "129730",
          "chgPct": "0.94"
        }
      }
    ]
  }
}
```

With `expiry=None`, `fut[]` contains every available expiry's contract; with
a specific `expiry`, it contains only that one.

## HTTP Request Details

- **Method**: GET
- **Endpoint**: `market-data/1.0/watchlist/option-chain`
- **Authentication**: `Authorization: <consumer_key>` header

## HTTP Response Details

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 400 | Invalid or missing input parameters (e.g. `count` not a multiple of 10) |
| 403 | Invalid session, please re-login |
| 429 | Too many requests to the API |
| 500 | Unexpected error |
