# **Totp_validate**
Totp validation is the final step in TOTP login flow.
Trade token is generated here with which the other apis are accessed.

```python
client.totp_validate(mpin="")
```

### Example


```python
from neo_api_client import NeoAPI


client = NeoAPI(environment='prod', access_token=None, neo_fin_key=None)

try:
    client.totp_validate(mpin="")

except Exception as e:
    print("Exception when calling TOTPLogin ->totp_validate: %s\n" % e)
```
### Parameters

| Name   | Description                                             | Type   |
|--------|---------------------------------------------------------|--------|
| *mpin* | Your Mobile Personal Identification Number Eg: "123456" | Str    |

### Return type

**object**

### Sample Response (Real API Response)
```json
{
  "data": {
    "token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    "sid": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "rid": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "baseUrl": "https://eXX.kotaksecurities.com",
    "hsServerId": "",
    "isUserPwdExpired": false,
    "ucc": "XXXXX",
    "greetingName": "USER_NAME",
    "isTrialAccount": false,
    "dataCenter": "E43",
    "derivativesRiskDisclosure": "Risk Disclosure on Derivatives\n\nAs per a SEBI study dated 25 Jan 2023- \n• 9 out of 10 individual traders in equity Futures and Options Segment, incurred net losses.",
    "mfAccess": 1,
    "dataCenterMap": null,
    "dormancyStatus": "A",
    "asbaStatus": "",
    "clientType": "RI",
    "isNRI": false,
    "kId": "XXXXXXXXXX",
    "kType": "Trade",
    "status": "success",
    "incRange": 0,
    "incUpdFlag": "",
    "clientGroup": "",
    "kraStatus": "",
    "rcFlag": 0
  }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `token` | string | JWT trade token (full access) |
| `sid` | string | Session ID |
| `rid` | string | Request ID |
| `baseUrl` | string | API base URL for the assigned data center |
| `ucc` | string | Unique Client Code |
| `greetingName` | string | User's name |
| `dataCenter` | string | Data center location (e.g., E43, GDC) |
| `kId` | string | Client PAN Card number |
| `kType` | string | Token type - "Trade" (full trading access) |
| `status` | string | Validation status - "success" or "failed" |
| `isUserPwdExpired` | boolean | Whether password has expired |
| `isTrialAccount` | boolean | Whether it's a trial account |
| `clientType` | string | Client type (e.g., "RI" for Retail Individual) |
| `isNRI` | boolean | Whether user is NRI (Non-Resident Indian) |
| `dormancyStatus` | string | Account dormancy status |

### Performance
- **Average Latency**: 134 ms
- **Typical Range**: 100-200 ms

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status Code | Description                               |
|-------------|-------------------------------------------|
| *200*       | Trade token generated                     |
| *400*       | Invalid or missing input parameters       |
| *429*       | Too many requests to the API              |
| *500*       | Unexpected error                          |
| *503*       | Trade API service is unavailable          |
| *504*       | Gateway timeout, trade API is unreachable |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)
