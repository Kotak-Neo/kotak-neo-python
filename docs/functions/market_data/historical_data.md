# Historical Data

Get historical candle data for an instrument.

## Function Signature

```python
client.historical_data(neosymbol, interval, from_date=None, to_date=None)
```

> **Note:** Requires `totp_validate()` to have been called first — see the
> [Expiries](./expiries.md) doc's note for why (URL resolution, not wire auth).

### Example

```python
from neo_api_client import NeoAPI

client = NeoAPI(consumer_key="your-token-from-neo-app", environment="prod")
client.totp_login(mobile_number="+919876543210", ucc="ABC123", totp="123456")
client.totp_validate(mpin="123456")

try:
    response = client.historical_data(
        neosymbol="nse_cm|1333",
        interval="10min",
        from_date="2026-08-20",
        to_date="2026-09-01",
    )
    print(response)
except Exception as e:
    print("Exception when calling historical_data: %s\n" % e)
```

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `neosymbol` | str | Yes | Instrument in `{exchange_segment}\|{instrument_token}` form, e.g. `nse_cm\|1333`. |
| `interval` | str | Yes | One of `1min`, `3min`, `5min`, `10min`, `15min`, `30min`, `60min`, `D` (daily), `W` (weekly). An unsupported value is rejected by the **backend** with `{"status": "ERROR", "fault": {"code": 400, "message": "Invalid interval value"}}` — not validated by the SDK. |
| `from_date` | str | No | Start date (`YYYY-MM-DD`). |
| `to_date` | str | No | End date (`YYYY-MM-DD`). |

### Date Range Limits (backend-enforced, not SDK-validated)

| Interval | Max Days | Example Use Case |
|----------|----------|------------------|
| 1min, 3min, 5min | 30 days | Intraday trading charts |
| 10min, 15min | 60 days | Short-term analysis |
| 30min, 60min | 90 days | Medium-term analysis |
| D (Daily) | 180 days | Long-term charts |
| W (Weekly) | 180 days | Trend analysis |

The SDK forwards whatever `interval`/`from_date`/`to_date` you pass straight
to the backend — it doesn't validate any of this itself. A request with an
unsupported interval, or a date range exceeding that interval's limit, is
rejected by the backend, not the SDK.

## Return Type

**dict**

## Sample Response

```json
{
  "status": "success",
  "interval": "1min",
  "data": {
    "candles": [
      ["2026-08-20T09:15:00+0530", 12009.9, 12019.35, 12001.25, 12001.5, 163275, 13667775],
      ["2026-08-20T09:16:00+0530", 12001, 12003, 11998.25, 12001, 105750, 13667775]
    ]
  }
}
```

Each entry in `candles` is a fixed-order positional row, **not** an object —
this is the key change from the legacy parallel-array response shape:

```
[timestamp, open, high, low, close, volume, oi]
```

- `timestamp` is ISO 8601.
- **Phase 1 note:** `oi` is not yet populated in the candle rows (planned for a later phase) — don't rely on it being present/non-null yet.

## HTTP Request Details

- **Method**: GET
- **Endpoint**: `market-data/1.0/historical/details`
- **Authentication**: `Authorization: <consumer_key>` header

## HTTP Response Details

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 400 | Invalid or missing input parameters (e.g. unsupported `interval`, or a date range exceeding that interval's limit) |
| 403 | Invalid session, please re-login |
| 429 | Too many requests to the API |
| 500 | Unexpected error |
