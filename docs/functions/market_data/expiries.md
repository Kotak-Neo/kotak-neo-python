# Expiries

Get available expiry dates for an exchange + underlying, in ISO (`YYYY-MM-DD`) format.

## Function Signature

```python
client.expiries(exchange, underlying, instrument_type=None)
```

> **Note:** Requires `totp_validate()` to have been called first. The wire
> call itself only needs `consumer_key` (same as `quotes()`) — but the SDK
> resolves this endpoint's URL from your account's `base_url`, which is
> only populated after `totp_validate()`. Calling this before then raises
> `ValueError`.

### Example

```python
from neo_api_client import NeoAPI

client = NeoAPI(consumer_key="your-token-from-neo-app", environment="prod")
client.totp_login(mobile_number="+919876543210", ucc="ABC123", totp="123456")
client.totp_validate(mpin="123456")

try:
    response = client.expiries(exchange="nse_fo", underlying="RELIANCE")
    print(response)
except Exception as e:
    print("Exception when calling expiries: %s\n" % e)
```

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `exchange` | str | Yes | Exchange segment, e.g. `nse_fo`, `mcx_fo`. |
| `underlying` | str | Yes | Underlying name, e.g. `RELIANCE`, `NIFTY`. Matches `pSymbolName` in the scrip master file. |
| `instrument_type` | str | No | `Option` or `Fut`. |

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
- **Authentication**: `Authorization: <consumer_key>` header (no session token needed on the wire — see the note above about why `totp_validate()` is still required by the SDK)

## HTTP Response Details

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 400 | Invalid or missing input parameters |
| 403 | Invalid session, please re-login |
| 429 | Too many requests to the API |
| 500 | Unexpected error |
