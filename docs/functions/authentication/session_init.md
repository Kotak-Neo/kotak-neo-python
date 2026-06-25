# **Session_Init**
Initiate trading session for a User

```python
client = NeoAPI(environment='prod', access_token=None, neo_fin_key=None)

```

### Example

```python
from neo_api_client import NeoAPI


#the session initializes when the following constructor is called
# Either you pass consumer_key and consumer_secret or you pass acsess_token
client = NeoAPI(environment='prod', access_token=None, neo_fin_key=None)
```
### Parameters

| Name                   | Description                                                   | Type           |
|------------------------|---------------------------------------------------------------|----------------|
| *access_token*         | Mandatory if not passing consumer key and secret              | Str [optional] |
| *environment*          | UAT/PROD, Default Value = "UAT"                               | Str [optional] |
| *neo_fin_key*          | Default Value = "neotradeapi"                                 | Str [optional] |


## Return type

**object**

### Sample response

```json
{
    "access_token": "",
    "scope": "default",
    "token_type": "Bearer",
    "expires_in": 8760000
}

### HTTP request headers

 - **Accept**: application/json

### HTTP response details

| Status Code | Description                                  |
|-------------|----------------------------------------------|
| *200*       | Ok                                           |
| *401*       | Invalid or missing input parameters          |


[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)
