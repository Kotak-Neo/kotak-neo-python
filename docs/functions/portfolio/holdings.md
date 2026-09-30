# **Holdings**
Get your current holdings

```python
client.holdings()
```

### Example

```python
from neo_api_client import NeoAPI


# First initialize session and generate session token
client = NeoAPI(environment="prod", access_token=None, neo_fin_key=None)
client.totp_login(mobilenumber="", ucc="", totp="")
client.totp_validate(mpin="")

try:
    client.holdings()
except Exception as e:
    print("Exception when calling Holdings->holdings: %s\n" % e)
```

### Return type

**object**

### Sample response
```json
{
    "data": [
        {
            "displaySymbol": "IDEA",
            "averagePrice": 9.5699,
            "quantity": 35,
            "exchangeSegment": "nse_cm",
            "exchangeIdentifier": "14366",
            "holdingCost": 334.9475,
            "mktValue": 327.6,
            "scripId": "746a0ebbc6295a002ab27e42a3e06a6792baeba1",
            "instrumentToken": 8658,
            "instrumentType": "Equity",
            "isAlternateScrip": false,
            "closingPrice": 9.36,
            "symbol": "IDEA",
            "sellableQuantity": 35
        }
    ]
}

```

### Always a live call — and what it feeds internally into `positions()`

A direct call to `holdings()` **always hits the network** — it's a live
read, never served from a cache. A successful call also refreshes a
same-day cache that `positions()` checks internally (see below), so calling
`holdings()` yourself right before calling `positions()` saves `positions()`
a redundant fetch.

`positions()` uses `averagePrice` (actual purchase cost) and
`exchangeIdentifier` (matching key) from Holdings to correctly compute
average price and P&L for equity carry-forward positions; the Positions API
alone doesn't carry that cost basis. To get this, `positions()` first checks
whether holdings has already been fetched **today** (by an earlier
`holdings()` call, or an earlier `positions()` call) — if so, it reuses that
cached result; if not, it fetches holdings itself (one network call) before
continuing. Either way, `positions()` itself never makes more than one
holdings fetch per calendar day — but a direct `holdings()` call you make is
never skipped, no matter how recently `positions()` fetched it. A failed
fetch is not cached, so the next call that needs holdings retries rather
than locking in an error for the rest of the day.

> **Note:** the cache `positions()` checks is persisted to disk, not just
> held in memory — TTL expires at midnight local time, default location
> `~/.kotak_neo/holdings_cache`, overridable via the
> `NEO_HOLDINGS_CACHE_DIR` environment variable, scoped per account (UCC).
> This means it survives across separate process runs, e.g. running the same
> script twice in a row the same day: the second run's `positions()` reuses
> the first run's holdings fetch instead of hitting the network again.

See
[Positions](positions.md#positions-calculations--computed-automatically) for
the full calculation this powers.

> **Match on `exchangeIdentifier`, not `instrumentToken`.** Both fields are
> present in the sample response above with *different* values (`14366` vs
> `8658`) — `instrumentToken` identifies the holding record itself, not the
> instrument for matching against `positions.tok`.

### Error handling

If the response body cannot be parsed as JSON (e.g. a `5xx` response with an empty or non-JSON body), `holdings()` does not raise — it returns a structured error dict instead:

```json
{
    "Error": "Unexpected response format",
    "Exception": "<str(JSONDecodeError)>",
    "StatusCode": 503,
    "ContentType": "text/html",
    "ResponseText": "<first 5000 characters of the raw response body>",
    "RequestURL": "<the request URL that was called>"
}
```

### HTTP request headers

 - **Accept**: */*


### HTTP response details
| Status Code | Description                                           |
|-------------|-------------------------------------------------------|
| *200*       | Gets the Portfolio holdings data for a client account |
| *400*       | Invalid or missing input parameters                   |
| *403*       | Invalid session, please re-login to continue          |
| *429*       | Too many requests to the API                          |
| *500*       | Unexpected error                                      |
| *502*       | Not able to communicate with OMS                      |
| *503*       | Trade API service is unavailable                      |
| *504*       | Gateway timeout, trade API is unreachable             |
