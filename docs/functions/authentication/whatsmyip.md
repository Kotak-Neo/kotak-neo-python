# What's My IP

Retrieve the client's outbound IP address as seen by the Kotak NEO backend.

## Function Signature

```python
client.whatsmyip()
```

## Description

The `whatsmyip()` function returns the public IP address the NEO server observes
for your requests, along with the server timestamp. This is useful for confirming
which IP would need to be whitelisted for IP-restricted access.

Requires a completed authentication flow (`totp_login` → `totp_validate`).

## Parameters

None

## Return Type

**dict** - Client IP response

## Example

```python
from neo_api_client import NeoAPI

# Initialize and login
client = NeoAPI(environment='prod', consumer_key='your-consumer-key')
client.totp_login(mobile_number='+919876543210', ucc='YOUR_UCC', totp='123456')
client.totp_validate(mpin='123456')

# Fetch the outbound IP seen by the server
response = client.whatsmyip()
print(response)
print("My IP:", response["data"][0]["ip"])
```

## Sample Response

```json
{
    "data": [
        {
            "ip": "165.85.130.248",
            "time": "2026-07-07 12:07:34.440"
        }
    ],
    "stCode": 1000,
    "status": "success"
}
```

## Response Parameters

| Name | Description |
|------|-------------|
| `data[].ip` | The client's outbound IP address as seen by the server |
| `data[].time` | Server timestamp when the request was processed |
| `stCode` | Status code (`1000` = success) |
| `status` | Status string (`"success"`) |

## Errors

| Condition | Response |
|-----------|----------|
| Called before 2FA is complete | `{"Error Message": "Complete the 2fa process before accessing this application"}` |
| API/network error (`ApiException`, caught inside the service layer) | `{"error": <ApiException>}` |
| Non-JSON response | `{"Error": "Unexpected response format. Expected JSON but received something else."}` |
| Any other unexpected exception (caught by the `whatsmyip()` wrapper) | `{"Error": <exception>}` |

## HTTP request headers

| Header | Value | Notes |
|--------|-------|-------|
| **Authorization** | `<consumer_key>` | The app-level key from `NeoAPI(consumer_key=...)`; sent as-is, no `Bearer` prefix |
| **Sid** | `<edit_sid>` | Trade session ID from `totp_validate` (post-2FA) |
| **Auth** | `<edit_token>` | Trade token from `totp_validate` (post-2FA) |
| **accept** | application/json | |

This is a `GET` request with no body, so no `Content-Type` header is sent.

[[Back to top]](#) [[Back to API list]](../README.md) [[Back to README]](../../../README.md)
