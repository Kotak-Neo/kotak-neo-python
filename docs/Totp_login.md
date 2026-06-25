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

### Sample response
```json
{
	"data": {
		"token": "",
		"sid": "",
		"rid": "",
		"hsServerId": "server4",
		"isUserPwdExpired": false,
		"ucc": "",
		"greetingName": "",
		"isTrialAccount": false,
		"dataCenter": "gdc",
		"searchAPIKey": "",
		"derivativesRiskDisclosure": "",
		"mfAccess": 1,
		"dataCenterMap": null,
		"dormancyStatus": "A",
		"asbaStatus": "",
		"clientType": "RI",
		"isNRI": false,
		"kId": "AVRPC7535J",
		"kType": "View",
		"status": "success",
		"incRange": 0,
		"incUpdFlag": "",
		"clientGroup": ""
	}
}
```

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
