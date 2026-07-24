# **Session_Init**

> **DEPRECATED / REMOVED:** The OAuth2 `session_init()` call (`LoginAPI.session_init()` in
> `neo_api_client/services/login.py`) is dead code. It is only referenced inside a commented-out
> line in the `NeoAPI.__init__` constructor (`neo_api_client/neo_api.py`) and is never invoked.
> Constructing `NeoAPI(...)` today performs **no HTTP request** — it only sets local
> configuration attributes (`consumer_key`, `environment`, `access_token`, `neo_fin_key`). The
> `consumer_key`/`consumer_secret` OAuth2 client-credentials flow and the sample OAuth token
> response shown below do not occur in the current SDK. The supported authentication flow is
> TOTP-based: initialize `NeoAPI(consumer_key=...)` then call
> [TOTP Login](./totp_login.md) followed by [TOTP Validate](./totp_validate.md). Everything
> below this notice is retained only as historical reference and does **not** reflect the
> current SDK — do not rely on it.

Initiate trading session for a User

```python
client = NeoAPI(environment="prod", access_token=None, neo_fin_key=None)
```

### Example

```python
from neo_api_client import NeoAPI


# the session initializes when the following constructor is called
# Either you pass consumer_key and consumer_secret or you pass acsess_token
client = NeoAPI(environment="prod", access_token=None, neo_fin_key=None)
```
### Parameters

| Name                   | Description                                                   | Type           |
|------------------------|---------------------------------------------------------------|----------------|
| *access_token*         | Mandatory if not passing consumer key and secret              | Str [optional] |
| *environment*          | Default Value = "prod"                                        | Str [optional] |
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
