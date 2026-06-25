# Logout

End the current trading session and invalidate the session tokens.

## Function Signature

```python
client.logout()
```

## Description

The `logout()` function terminates the current trading session by clearing all session tokens (bearer token, edit token, and session IDs). This is important for security and should be called when trading activities are complete.

## Parameters

None

## Return Type

**dict** - Logout status response

## Example

```python
from neo_api_client import NeoAPI

# Initialize and login
client = NeoAPI(environment='prod', consumer_key='your-consumer-key')
client.totp_login(mobile_number='+919876543210', ucc='YOUR_UCC', totp='123456')
client.totp_validate(mpin='123456')

# Perform trading operations...

# Logout when done
try:
    response = client.logout()
    print(response)
except Exception as e:
    print(f"Exception when calling logout: {e}")
```

## Response

### Success Response

```json
{
  "State": "OK",
  "message": "You have been successfully logged out"
}
```

### Error Response

```json
{
  "State": "NOT_OK",
  "message": "Some Exception with the Logout Functionality"
}
```

### Pre-Login Error

```json
{
  "Error Message": "Complete the 2fa process before accessing this application"
}
```

## HTTP Request Details

- **Method**: Internal cleanup (no HTTP request)
- **Authentication**: Requires valid session tokens

## Response Details

| Status | Description |
|--------|-------------|
| `State: OK` | Successfully logged out |
| `State: NOT_OK` | Logout failed |

## Performance

- **Average Latency**: < 1 ms (local operation)

## Notes

- This function clears local session tokens
- After logout, you must complete the login flow again to perform trading operations
- Always call logout when your trading session is complete for security
- WebSocket connections should be closed before calling logout

## Related Functions

- [TOTP Login](./totp_login.md) - Login to start a new session
- [TOTP Validate](./totp_validate.md) - Complete 2FA authentication

## Best Practices

```python
try:
    # Your trading code here
    pass
finally:
    # Always logout, even if errors occur
    client.logout()
    
    # Close WebSocket if used
    if client.NeoWebSocket and client.NeoWebSocket.hsWebsocket:
        client.NeoWebSocket.hsWebsocket.close()
```

[[Back to top]](#) [[Back to API list]](../README.md) [[Back to README]](../../../README.md)
