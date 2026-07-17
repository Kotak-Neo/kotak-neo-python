# **Totp_login**

TOTP login is the first step in TOTP authentication flow where the view token is generated.

## Prerequisites

### 1. Get Consumer Key
- Login to Kotak NEO app/web
- Navigate to **Invest** tab → **Trade API** card
- Click **Generate application**
- Copy the token shown with the default application
- Use this token as `consumer_key` when initializing `NeoAPI`

### 2. Register for TOTP (One-time setup)
- Visit https://www.kotaksecurities.com/platform/kotak-neo-trade-api/
- Click **Register for TOTP**
- Verify mobile with OTP
- Select account for TOTP registration
- Scan QR code with authenticator app (Google Authenticator, Authy, etc.)
- Save the secret key from QR code (for automated TOTP generation)
- Submit TOTP to complete registration

## Usage

```python
client.totp_login(mobile_number="", ucc="", totp='')
```

### Example

```python
from neo_api_client import NeoAPI

# Initialize with consumer key from NEO app Trade API card
client = NeoAPI(
    consumer_key='your-consumer-key-token',  # Required: Token from NEO app
    environment='prod',
    access_token=None,
    neo_fin_key=None
)

try:
    # Login with TOTP
    response = client.totp_login(
        mobile_number="+919876543210",  # Registered mobile with country code
        ucc="ABC123",  # Your UCC from NEO app Profile
        totp='123456'  # 6-digit code from authenticator app
    )
    print(response)

except Exception as e:
    print("Exception when calling totp_login: %s\n" % e)
```

### Parameters

| Name           | Description                                           | Type   |
|----------------|-------------------------------------------------------|--------|
| *mobile_number* | Your registered mobile number with country code. Example: "+919876543210" | Str    |
| *ucc*          | Your Unique Client Code. Find in NEO app under Profile section. Example: "ABC123" | Str    |
| *totp* | 6-digit Time-based One-Time Password from authenticator app. Changes every 30 seconds. Example: "123456" | Str    |

### Return type

**object**

### Sample Response (Real API Response)
```json
{
  "data": {
    "token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    "sid": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "rid": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "isUserPwdExpired": false,
    "ucc": "XXXXX",
    "greetingName": "USER_NAME",
    "isTrialAccount": false,
    "dataCenter": "E43",
    "derivativesRiskDisclosure": "Risk Disclosure on Derivatives\n\nAs per a SEBI study dated 25 Jan 2023- \n• 9 out of 10 individual traders in equity Futures and Options Segment, incurred net losses.\n• On an average, loss makers registered net trading loss close to Rs.50,000.\n• Over and above the net trading losses incurred, loss makers expended an additional 28% of net trading losses as transaction costs.\n• Those making net trading profits, incurred between 15% to 50% of such profits as transaction cost.\n\nFor more information please check out : https://www.sebi.gov.in/reports-and-statistics/research/jan-2023/study-analysis-of-profit-and-loss-of-individual-traders-dealing-in-equity-fando-segment_67525.html",
    "mfAccess": 1,
    "dataCenterMap": null,
    "dormancyStatus": "A",
    "asbaStatus": "",
    "clientType": "RI",
    "isNRI": false,
    "kId": "XXXXXXXXXX",
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
| `kId` | string | Client PAN Card number |
| `kType` | string | Token type - "View" (needs 2FA for "Trade" access) |
| `status` | string | Login status - "success" or "failed" |
| `isUserPwdExpired` | boolean | Whether password has expired |
| `isTrialAccount` | boolean | Whether it's a trial account |
| `clientType` | string | Client type (e.g., "RI" for Retail Individual) |
| `isNRI` | boolean | Whether user is NRI (Non-Resident Indian) |
| `dormancyStatus` | string | Account dormancy status |
| `derivativesRiskDisclosure` | string | SEBI risk disclosure message for derivatives trading |

### Error response

A blank/missing `mobile_number`, `ucc`, or `totp` is rejected client-side (no network call), using the same error shape the backend itself returns for this case:

```json
{
    "error": [
        {
            "code": "400",
            "message": "Missing required field 'MobileNumber'"
        }
    ]
}
```

The `message` names whichever field is missing (`'MobileNumber'`, `'Ucc'`, or `'Totp'`).

### Performance
- **Average Latency**: 367 ms
- **Typical Range**: 300-450 ms

### HTTP request headers

| Header | Value | Notes |
|--------|-------|-------|
| **Authorization** | `<consumer_key>` | The app-level key from `NeoAPI(consumer_key=...)`; sent as-is, no `Bearer` prefix |
| **neo-fin-key** | `<neo_fin_key>` | Only present if `neo_fin_key` was passed to `NeoAPI(...)` |
| **Content-Type** | application/json | |
| **Accept** | application/json | |

`totp_login` is the very first call in the auth flow — no `sid`/`Auth` (session/token)
headers are sent yet, since neither exists until this call returns.

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
