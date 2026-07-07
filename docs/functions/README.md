# API Functions Documentation

Complete reference for all Kotak Neo Python SDK functions with examples and real API responses.

## Getting Started

Before using any API functions, you must:

1. **Get Consumer Key** - Login to NEO app → Invest → Trade API → Generate application
2. **Initialize Client** - Create NeoAPI instance with consumer_key
3. **Authenticate** - Complete TOTP login and MPIN validation

```python
from neo_api_client import NeoAPI

# Initialize with consumer key (REQUIRED)
client = NeoAPI(
    consumer_key='your-token-from-neo-app',
    environment='prod'
)

# Authenticate
client.totp_login(mobile_number='+919876543210', ucc='ABC123', totp='123456')
client.totp_validate(mpin='123456')

# Now you can use all API functions
```

## Table of Contents

### 1. Authentication
- [TOTP Login](./authentication/totp_login.md) - Initiate TOTP-based login
- [TOTP Validate](./authentication/totp_validate.md) - Complete 2FA with MPIN
- [What's My IP](./authentication/whatsmyip.md) - Get the client's outbound IP as seen by the server
- [Logout](./authentication/logout.md) - End trading session

### 2. Order Management
- [Place Order](./orders/place_order.md) - Place new orders (Regular/AMO/Bracket/Cover)
- [Modify Order](./orders/modify_order.md) - Modify existing orders
- [Cancel Order](./orders/cancel_order.md) - Cancel regular orders
- [Order Report](./orders/order_report.md) - Get order book
- [Order History](./orders/order_history.md) - Get order history
- [Trade Report](./orders/trade_report.md) - Get executed trades

### 3. Portfolio & Positions
- [Holdings](./portfolio/holdings.md) - Get portfolio holdings
- [Positions](./portfolio/positions.md) - Get current positions
- [Limits](./portfolio/limits.md) - Check available limits
- [Margin Required](./portfolio/margin_required.md) - Calculate margin for orders

### 4. Market Data
- [Quotes](./market_data/quotes.md) - Get real-time quotes
- [Scrip Master](./market_data/scrip_master.md) - Download scrip master files
- [Search Scrip](./market_data/search_scrip.md) - Search for instruments

### 5. WebSocket (SFeed, async/await — v2.2.0+)
- [Subscribe](./websocket/subscribe.md) - Subscribe to live market feed
- [Unsubscribe](./websocket/unsubscribe.md) - Unsubscribe from feed
- [Order Feed](./websocket/order_feed.md) - Legacy order feed (removed in v2.2.0)
- [SFeed WebSocket Guide](../guides/websocket.md) - Full async client reference & migration

## Quick Links

- [Installation Guide](../installation/README.md)
- [Main README](../../README.md)
- [GitHub Repository](https://github.com/Kotak-Neo/kotak-neo-python)

## Response Format

All API responses follow consistent patterns:

### Success Response
```json
{
  "data": { /* response data */ },
  "stat": "Ok",
  "stCode": 200
}
```

### Error Response
```json
{
  "error": [
    {
      "code": "error_code",
      "message": "Error description"
    }
  ],
  "stat": "Not_Ok"
}
```

### No Data Response
```json
{
  "stCode": 5203,
  "errMsg": "No Data",
  "desc": "data not found",
  "stat": "Not_Ok"
}
```

## Common Parameters

### Exchange Segments
- `nse_cm` - NSE Cash Market
- `bse_cm` - BSE Cash Market
- `nse_fo` - NSE Futures & Options
- `bse_fo` - BSE Futures & Options
- `cde_fo` - Currency Derivatives
- `mcx_fo` - MCX Commodities

### Product Types
- `CNC` - Cash & Carry (Delivery)
- `MIS` - Margin Intraday Square-off
- `NRML` - Normal (Carry Forward)

### Order Types
- `L` - Limit Order
- `MKT` - Market Order
- `SL` - Stop Loss Limit
- `SL-M` - Stop Loss Market

### Transaction Types
- `B` - Buy
- `S` - Sell

### Validity Types
- `DAY` - Valid for the day
- `IOC` - Immediate or Cancel

## Performance Benchmarks

Average API latency (production environment):

| Function | Avg Latency |
|----------|-------------|
| TOTP Login | 367 ms |
| TOTP Validate | 134 ms |
| Quotes | 289 ms |
| Order Report | 71 ms |
| Trade Report | 67 ms |
| Positions | 68 ms |
| Holdings | 73 ms |
| Limits | 77 ms |
| Margin Required | 110 ms |
| Scrip Master | 1250 ms |
| Search Scrip | 2176 ms |

## Support

For issues or questions:
- GitHub Issues: https://github.com/Kotak-Neo/kotak-neo-python/issues
- Email: support@kotakneo.com
