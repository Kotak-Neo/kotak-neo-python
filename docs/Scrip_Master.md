# **Scrip_Master**
Get ScripMaster CSV file

```python
client.scrip_master()
```

To get ScripMaster file of a particular segment, pass the exchange segment within bracket. For example - `client.scripmaster(nse_cm)`

### Example

```python

from neo_api_client import NeoAPI


#First initialize session and generate session token
client = NeoAPI(environment='prod', access_token=None, neo_fin_key=None)
client.totp_login(mobilenumber="", ucc="", totp='')
client.totp_validate(mpin="")

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
    "filesPaths": [
        "https://lapi.kotaksecurities.com/wso2-scripmaster/v1/prod/2025-01-22/transformed/bse_cm.csv",
        "https://lapi.kotaksecurities.com/wso2-scripmaster/v1/prod/2025-01-22/transformed/cde_fo.csv",
        "https://lapi.kotaksecurities.com/wso2-scripmaster/v1/prod/2025-01-22/transformed/mcx_fo.csv",
        "https://lapi.kotaksecurities.com/wso2-scripmaster/v1/prod/2025-01-22/transformed/nse_cm.csv",
        "https://lapi.kotaksecurities.com/wso2-scripmaster/v1/prod/2025-01-22/transformed/nse_fo.csv",
        "https://lapi.kotaksecurities.com/wso2-scripmaster/v1/prod/2025-01-22/transformed/bse_fo.csv"
    ],
    "baseFolder": "https://lapi.kotaksecurities.com/wso2-scripmaster/v1/prod"
}
```

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
