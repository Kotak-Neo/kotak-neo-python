# Expiries

Get available expiry dates for an exchange + underlying, in ISO (`YYYY-MM-DD`) format.

## Function Signature

```python
client.expiries(exchange, underlying, instrument_type=None)
```

> **Note:** Like `quotes()`, this does not require a completed 2FA (TOTP)
> session — only `consumer_key` is required, since the underlying API
> authenticates via the `Authorization` header alone.

### Example

```python
from neo_api_client import NeoAPI

# Only consumer_key is required — no totp_login/totp_validate needed
client = NeoAPI(consumer_key="your-token-from-neo-app", environment="prod")

try:
    response = client.expiries(exchange="nse_fo", underlying="RELIANCE")
    print(response)
except Exception as e:
    print("Exception when calling expiries: %s\n" % e)
```

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `exchange` | str | Yes | Exchange segment. One of `nse_fo`, `bse_fo`, `mcx_fo`. |
| `underlying` | str | Yes | Underlying name, e.g. `RELIANCE`, `NIFTY`. Matches `pSymbolName` in the scrip master file. |
| `instrument_type` | str | No | `option` or `fut`. |

## Return Type

**dict**

## Sample Response

```json
{
  "exchange": "nse_fo",
  "underlying": "RELIANCE",
  "expiries": [
    "2026-06-25",
    "2026-06-30",
    "2026-07-31"
  ]
}
```

`expiries` is a flat array of ISO date strings, sorted ascending. Pass one of
these directly as `option_chain()`'s `expiry` parameter.

## HTTP Request Details

- **Method**: GET
- **Endpoint**: `market-data/1.0/watchlist/expiries`
- **Authentication**: `Authorization: <consumer_key>` header (no session token needed)

## HTTP Response Details

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 400 | Invalid or missing input parameters |
| 403 | Invalid session, please re-login |
| 429 | Too many requests to the API |
| 500 | Unexpected error |
