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

### Sample response
```json
{
	"data": {
		"token": "",
		"sid": "",
		"rid": "",
		"hsServerId": "",
		"isUserPwdExpired": false,
		"ucc": "",
		"greetingName": "",
		"isTrialAccount": false,
		"dataCenter": "",
		"searchAPIKey": "",
		"derivativesRiskDisclosure": "",
		"mfAccess": 1,
		"dataCenterMap": null,
		"dormancyStatus": "A",
		"asbaStatus": "",
		"clientType": "RI",
		"isNRI": false,
		"kId": "",
		"kType": "Trade",
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
| *200*       | Trade token generated                     |
| *400*       | Invalid or missing input parameters       |
| *429*       | Too many requests to the API              |
| *500*       | Unexpected error                          |
| *503*       | Trade API service is unavailable          |
| *504*       | Gateway timeout, trade API is unreachable |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)
