# **Session_2fa**
Generate final Session Token for the user

```python
client.session_2fa(OTP="")
```

### Example

```python
from neo_api_client import NeoAPI

client = NeoAPI(environment="uat")

try:
    # Login using password
    client.login(mobilenumber="", password="")

    # Generate final Session Token
    client.session_2fa(OTP="")

except Exception as e:
    print("Exception when calling SessionApi->session_2fa: %s\n" % e)
```

### Parameters


| Name           | Description                                                        | Type   |
|----------------|--------------------------------------------------------------------|--------|
| *mobilenumber* | Your registered mobile number Eg: "+919999996708"                  | Str    |
| *pan*          | Your PAN number Eg: “DUMMY1234A”                                   | Str    |
| *password*     | Your trading password                                              | Str    |
| *otp*          | The 4-digit code you receive on registered mobile number           | Str    |


### Return type

object

### Sample Response

```json
{
  "data": {
    "token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    "sid": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "rid": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "isUserPwdExpired": false,
    "caches": {
      "baskets": "1687845385",
      "lastUpdatedTS": "1687845385",
      "multiplewatchlists": "1683352919",
      "techchartpreferences": "1683528608"
    },
    "ucc": "XXXXX",
    "greetingName": "USER_NAME",
    "isTrialAccount": false,
    "dataCenter": "gdc",
    "searchAPIKey": ""
  }
}
```

**Note:** This is a legacy authentication method. For new implementations, please use [TOTP Login](./totp_login.md) and [TOTP Validate](./totp_validate.md).

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status Code | Description                               |
|-------------|-------------------------------------------|
| *200*       | User session validated successfully       |
| *400*       | Invalid or missing input parameters       |
| *401*       | Verify resource and path of the request   |
| *429*       | Too many requests to the API              |
| *500*       | Unexpected error                          |
| *502*       | Not able to communicate with OMS          |
| *503*       | Trade API service is unavailable          |
| *504*       | Gateway timeout, trade API is unreachable |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)
