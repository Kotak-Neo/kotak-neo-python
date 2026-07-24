# **Scrip_Master**
Get ScripMaster CSV file

```python
client.scrip_master()
```

To get the ScripMaster file of a particular segment, pass the exchange segment. For example:

```python
client.scrip_master(exchange_segment="nse_cm")
```

```json
"https://lapi.kotaksecurities.com/wso2-scripmaster/v1/prod/2026-07-14/transformed-v1/nse_cm-v1.csv"
```

This returns just the matching file's URL (a string), not the CSV content itself — the caller is responsible for downloading it (this is what `search_scrip()` does internally).

> **Note:** Unlike most trading/portfolio methods, `scrip_master()` does not require a completed 2FA (TOTP) session — only `consumer_key` is required, since the underlying API authenticates via the `Authorization` header alone.

### Example

```python
from neo_api_client import NeoAPI


# Only consumer_key is required — no totp_login/totp_validate needed
client = NeoAPI(environment="prod", consumer_key="your_consumer_key")

try:
    client.scrip_master()
except Exception as e:
    print("Exception when calling Scrip Master Api->scrip_master: %s\n" % e)
```

### Return type

**object**

### Sample response

```json
{
    "baseFolder": "https://lapi.kotaksecurities.com/wso2-scripmaster/v1/prod",
    "filesPaths": [
        "https://lapi.kotaksecurities.com/wso2-scripmaster/v1/prod/2026-07-14/transformed/cde_fo.csv",
        "https://lapi.kotaksecurities.com/wso2-scripmaster/v1/prod/2026-07-14/transformed/mcx_fo.csv",
        "https://lapi.kotaksecurities.com/wso2-scripmaster/v1/prod/2026-07-14/transformed/nse_fo.csv",
        "https://lapi.kotaksecurities.com/wso2-scripmaster/v1/prod/2026-07-14/transformed/bse_fo.csv",
        "https://lapi.kotaksecurities.com/wso2-scripmaster/v1/prod/2026-07-14/transformed/nse_com.csv",
        "https://lapi.kotaksecurities.com/wso2-scripmaster/v1/prod/2026-07-14/transformed-v1/bse_cm-v1.csv",
        "https://lapi.kotaksecurities.com/wso2-scripmaster/v1/prod/2026-07-14/transformed-v1/nse_cm-v1.csv"
    ]
}
```

> **Note:** The folder is date-stamped (changes daily) and file naming varies by
> segment/version — e.g. `nse_cm` and `bse_cm` are currently served from a
> `transformed-v1` folder as `nse_cm-v1.csv` / `bse_cm-v1.csv`, while other
> segments are served from `transformed` with plain names (note `nse_com.csv`,
> not `nse_cm.csv`, for the older-format NSE CM file). Always resolve the exact
> filename from this response rather than hardcoding a path.

### HTTP request headers

 - **Accept**: application/json


### HTTP response details
| Status Code | Description                                  |
|-------------|----------------------------------------------|
| *200*       | Ok                                           |
| *400*       | Invalid or missing input parameters          |
| *403*       | Invalid session, please re-login to continue |
| *429*       | Too many requests to the API                 |
| *500*       | Unexpected error                             |
| *502*       | Not able to communicate with OMS             |
| *503*       | Trade API service is unavailable             |
| *504*       | Gateway timeout, trade API is unreachable    |
