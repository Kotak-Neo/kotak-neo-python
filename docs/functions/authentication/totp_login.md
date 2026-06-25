# **Totp_login**
TOTP login is the third step in TOTP login flow where view token is generated.

```python
client.totp_login(mobilenumber="", ucc="", totp='')
```

### Example


```python
from neo_api_client import NeoAPI


client = NeoAPI(environment='prod', access_token=None, neo_fin_key=None)


try:
    client.totp_login(mobilenumber="", ucc="", totp='')

except Exception as e:
    print("Exception when calling TOTPLogin ->login: %s\n" % e)
```
### Parameters

| Name           | Description                                           | Type   |
|----------------|-------------------------------------------------------|--------|
| *mobilenumber* | Your registered mobile number Eg: "+919999996708"     | Str    |
| *ucc*          | Your unique client code Eg: "ABC12"                   | Str    |
| *totp* | TOTP recieved on google authenticator app Eg: "123456" | Str    |

### Return type

**object**

### Sample Response (Real API Response)
```json
{
  "data": {
    "token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiIwM2FlMDlhMC0xMTczLTQwYWMtYWM3ZC01Yzk4ZTY0YjkwNzEiLCJpc3MiOiJsb2dpbi1zZXJ2aWNlIiwic3ViIjoiMjJmNGNkNGMtOGFjNy00NTdiLWFmZDMtYjFiZGNlMTU1YmIxIiwidWNjIjoiWFhDTTMiLCJuYXAiOiIiLCJ5Y2UiOiJlWVxcNiBcIiw1LnRcdTAwMDRcblx1MDAwN35cdTAwMDBcdTAwMTBiIiwiY2F0ZWdvcmlzYXRpb24iOiIiLCJzY29wZSI6WyJWaWV3Il0sImV4cCI6MTc4MjQxMjIwMCwiaWF0IjoxNzgyMzc0NjU3LCJmZXRjaGNhY2hpbmdydWxlIjowfQ.ilglfQzfJk0aYpgFB1YXE1vvgBX8K0S-ZYmny8vKXkTRYGd_b8qy5czfJ-dprsQRAtVCXPpKEURrnwuidWrKO0-Nisv-ZA1OE0t3HEgppwDFPagEYKxGTHT6q9y9j7EWhIpI3FoTcgPBtB02cU7SVRyE6RcN-Ljp1pUlUT8kDatLTgUGoWCY5YOqBYnQ5NWu14uoBRONgTg-klXYTdukYjJBA824Hn0R6ZTWAga-0NtkXS_ozeH-GRPDHBp8Xnpj_HtevW8eP3GWosQTbhS9ApjsH87SxxVa2JGZecl2vw7RbzCLCtkb_QMsxHOcW3AL1pX9b19iYcNvzJ8LeNDqzw",
    "sid": "21436d9a-4396-4350-ad8b-02a1c0058906",
    "rid": "9a761f31-f1f4-411c-a769-c51adb5a7515",
    "hsServerId": "",
    "isUserPwdExpired": false,
    "ucc": "XXCM3",
    "greetingName": "DHRUV",
    "isTrialAccount": false,
    "dataCenter": "E43",
    "derivativesRiskDisclosure": "Risk Disclosure on Derivatives\n\nAs per a SEBI study dated 25 Jan 2023- \n• 9 out of 10 individual traders in equity Futures and Options Segment, incurred net losses.\n• On an average, loss makers registered net trading loss close to Rs.50,000.\n• Over and above the net trading losses incurred, loss makers expended an additional 28% of net trading losses as transaction costs.\n• Those making net trading profits, incurred between 15% to 50% of such profits as transaction cost.\n\nFor more information please check out : https://www.sebi.gov.in/reports-and-statistics/research/jan-2023/study-analysis-of-profit-and-loss-of-individual-traders-dealing-in-equity-fando-segment_67525.html",
    "mfAccess": 1,
    "dataCenterMap": null,
    "dormancyStatus": "A",
    "asbaStatus": "",
    "clientType": "RI",
    "isNRI": false,
    "kId": "AIBPA4432H",
    "kType": "View",
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
| `token` | string | JWT view token (read-only access) |
| `sid` | string | Session ID |
| `rid` | string | Request ID |
| `ucc` | string | Unique Client Code |
| `greetingName` | string | User's name |
| `dataCenter` | string | Data center location (e.g., E43, GDC) |
| `kType` | string | Token type - "View" (needs 2FA for "Trade" access) |
| `status` | string | Login status - "success" or "failed" |
| `isUserPwdExpired` | boolean | Whether password has expired |
| `isTrialAccount` | boolean | Whether it's a trial account |
| `clientType` | string | Client type (e.g., "RI" for Retail Individual) |
| `isNRI` | boolean | Whether user is NRI |
| `dormancyStatus` | string | Account dormancy status |

### Performance
- **Average Latency**: 367 ms
- **Typical Range**: 300-450 ms

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status Code | Description                               |
|-------------|-------------------------------------------|
| *200*       | User session validated successfully       |
| *400*       | Invalid or missing input parameters       |
| *429*       | Too many requests to the API              |
| *500*       | Unexpected error                          |
| *503*       | Trade API service is unavailable          |
| *504*       | Gateway timeout, trade API is unreachable |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)
