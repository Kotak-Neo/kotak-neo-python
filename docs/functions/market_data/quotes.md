# Quotes

Get real-time market quotes for one or multiple instruments including price, volume, OHLC data, and market depth.

## Function Signature

```python
client.quotes(instrument_tokens, quote_type="all")
```

> **Note:** Unlike most trading/portfolio methods, `quotes()` does not require a completed 2FA (TOTP) session — only `consumer_key` is required, since the underlying API authenticates via the `Authorization` header alone.

### Example

```python
from neo_api_client import NeoAPI

# Only consumer_key is required — no totp_login/totp_validate needed
client = NeoAPI(consumer_key="your-token-from-neo-app", environment="prod")

# Get quotes for one or more instruments in a single call
instrument_tokens = [
    {"instrument_token": "1333", "exchange_segment": "nse_cm"},  # HDFCBANK
    {"instrument_token": "2885", "exchange_segment": "nse_cm"},  # RELIANCE
]

try:
    response = client.quotes(instrument_tokens=instrument_tokens, quote_type="all")
    print(response)
except Exception as e:
    print("Exception when calling quotes: %s\n" % e)
```

> **Multiple instruments:** Pass multiple entries in `instrument_tokens` to fetch quotes for several instruments in a single request. The SDK combines them the same way the REST API expects, e.g. two tokens become one request to `.../neosymbol/nse_cm|1333,nse_cm|2885/all`.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `instrument_tokens` | list | Yes | List of instrument dictionaries. Supports one or many instruments per call. |
| `quote_type` | str | No | Type of quote data to fetch (default: 'all') |

### Quote Types
- `all` - Complete quote data (default)
- `market_depth` - Market depth (order book)
- `ohlc` - Open, High, Low, Close
- `ltp` - Last Traded Price
- `oi` - Open Interest (for derivatives)
- `52w` - 52-week high/low
- `circuit_limits` - Circuit limit information
- `scrip_details` - Basic scrip information

### Instrument Token Format
```python
[{"instrument_token": "1333", "exchange_segment": "nse_cm"}]
```

## Return Type

**list** - List of quote dictionaries

## Sample Response (Real API Response)

```json
[
  {
    "exchange_token": "1333",
    "display_symbol": "HDFCBANK-EQ",
    "exchange": "nse_cm",
    "lstup_time": "1782374657",
    "ltp": "801.6000",
    "last_traded_quantity": "550",
    "total_buy": "907335",
    "total_sell": "2883870",
    "last_volume": "30043533",
    "avg_cost": "799.8900",
    "open_int": "0",
    "change": "8.4000",
    "per_change": "1.0600",
    "low_price_range": "713.9000",
    "high_price_range": "872.5000",
    "year_high": "2037.7",
    "year_low": "726.65",
    "ohlc": {
      "open": "798.5000",
      "high": "804.4500",
      "low": "796.0000",
      "close": "793.2000"
    },
    "depth": {
      "buy": [
        {
          "price": "801.6000",
          "quantity": "1733",
          "orders": "4"
        },
        {
          "price": "801.5500",
          "quantity": "490",
          "orders": "1"
        },
        {
          "price": "801.5000",
          "quantity": "623",
          "orders": "4"
        },
        {
          "price": "801.4500",
          "quantity": "645",
          "orders": "3"
        },
        {
          "price": "801.4000",
          "quantity": "723",
          "orders": "3"
        }
      ],
      "sell": [
        {
          "price": "801.6500",
          "quantity": "550",
          "orders": "1"
        },
        {
          "price": "801.7500",
          "quantity": "4383",
          "orders": "10"
        },
        {
          "price": "801.8000",
          "quantity": "3393",
          "orders": "6"
        },
        {
          "price": "801.8500",
          "quantity": "5449",
          "orders": "25"
        },
        {
          "price": "801.9000",
          "quantity": "5900",
          "orders": "13"
        }
      ]
    }
  }
]
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `exchange_token` | string | Instrument token |
| `display_symbol` | string | Display symbol (e.g., HDFCBANK-EQ) |
| `exchange` | string | Exchange segment |
| `ltp` | string | Last Traded Price |
| `last_traded_quantity` | string | Last traded quantity |
| `total_buy` | string | Total buy quantity |
| `total_sell` | string | Total sell quantity |
| `last_volume` | string | Total volume traded |
| `avg_cost` | string | Volume weighted average price |
| `change` | string | Price change from previous close |
| `per_change` | string | Percentage change |
| `year_high` | string | 52-week high |
| `year_low` | string | 52-week low |
| `ohlc` | object | Open, High, Low, Close prices |
| `depth` | object | Market depth with 5 levels of buy/sell orders |

## Performance

- **Average Latency**: 289 ms
- **Typical Range**: 250-350 ms

## HTTP Request Details

- **Method**: GET
- **Endpoint**: `/script-details/1.0/quotes/neosymbol/{exchange}|{token}[,{exchange}|{token}...]/{quote_type}`
- **Authentication**: Requires consumer_key in header

## HTTP Response Details

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 400 | Invalid or missing input parameters |
| 403 | Invalid session, please re-login |
| 429 | Too many requests to the API |
| 500 | Unexpected error |
| 502 | Not able to communicate with OMS |
| 503 | Trade API service is unavailable |
| 504 | Gateway timeout |
