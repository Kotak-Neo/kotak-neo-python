# Kotak Neo API - Python SDK

Official Python SDK for Kotak Neo Trading APIs - A production-ready, enterprise-grade trading client for the Kotak Neo platform.

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![PyPI Version](https://img.shields.io/badge/pypi-v2.1.1-green.svg)](https://pypi.org/project/kotakneoapi/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## Features

✅ **Authentication** - TOTP-based secure login with 2FA  
✅ **Order Management** - Place, modify, cancel orders (Regular/AMO/Bracket/Cover)  
✅ **Portfolio & Positions** - Real-time holdings, positions, and limits  
✅ **Market Data** - Live quotes, scrip master, search functionality  
✅ **WebSocket Streaming** - Real-time market feed and order updates  
✅ **Enterprise-Grade Reliability** - Circuit breaker, rate limiting, retry logic  
✅ **Comprehensive Error Handling** - Detailed exception hierarchy  
✅ **Type Safety** - Full mypy type checking support  
✅ **Extensive Testing** - Unit, integration, and E2E tests  

## Installation

### For Development (Local Installation)

Since this package is not yet published to PyPI, install it locally:

```bash
# Clone the repository
git clone https://github.com/Kotak-Neo/kotak-neo-python.git
cd kotak-neo-python

# Install in development/editable mode
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

### From PyPI (When Published)

```bash
pip install kotakneoapi
```

**Note:** The package is currently in development. For production use, install from the local repository as shown above.

## Quick Start

```python
from neo_api_client import NeoAPI

# Initialize the client
client = NeoAPI(
    environment='prod',  # or 'uat' for testing
    consumer_key='your-consumer-key',
    neo_fin_key='your-fin-key'  # optional, for tracking
)

# Login with TOTP
login_response = client.totp_login(
    mobile_number='+919876543210',
    ucc='YOUR_UCC',
    totp='123456'  # 6-digit TOTP from authenticator app
)

# Complete 2FA with MPIN
validate_response = client.totp_validate(mpin='123456')

# Place an order
order_response = client.place_order(
    exchange_segment='nse_cm',
    product='CNC',
    price='1500.00',
    order_type='L',
    quantity='10',
    validity='DAY',
    trading_symbol='RELIANCE-EQ',
    transaction_type='B'
)

# Get real-time quotes
quotes = client.quotes(
    instrument_tokens=[
        {'instrument_token': '1333', 'exchange_segment': 'nse_cm'}
    ],
    quote_type='all'
)

# Logout
client.logout()
```

## Documentation

### 📚 [Complete API Documentation](docs/functions/README.md)

Detailed documentation for all SDK functions with examples and real API responses.

#### Quick Links

**Authentication**
- [TOTP Login](docs/functions/authentication/totp_login.md) | [TOTP Validate](docs/functions/authentication/totp_validate.md) | [Logout](docs/functions/authentication/logout.md)

**Order Management**
- [Place Order](docs/functions/orders/place_order.md) | [Modify Order](docs/functions/orders/modify_order.md) | [Cancel Order](docs/functions/orders/cancel_order.md)
- [Order Report](docs/functions/orders/order_report.md) | [Order History](docs/functions/orders/order_history.md) | [Trade Report](docs/functions/orders/trade_report.md)

**Portfolio & Positions**
- [Holdings](docs/functions/portfolio/holdings.md) | [Positions](docs/functions/portfolio/positions.md)
- [Limits](docs/functions/portfolio/limits.md) | [Margin Required](docs/functions/portfolio/margin_required.md)

**Market Data**
- [Quotes](docs/functions/market_data/quotes.md) | [Scrip Master](docs/functions/market_data/scrip_master.md) | [Search Scrip](docs/functions/market_data/search_scrip.md)

**WebSocket**
- [Subscribe](docs/functions/websocket/subscribe.md) | [Unsubscribe](docs/functions/websocket/unsubscribe.md) | [Order Feed](docs/functions/websocket/order_feed.md)

### 📖 Guides & Documentation

**Installation:**
- **[Installation Overview](docs/installation/README.md)** - All installation options
- **[Installation Reference](docs/guides/INSTALLATION_REFERENCE.md)** - Complete platform guide
- **[Local Installation](docs/installation/local-install.md)** - Current method (before PyPI publish)
- **[Platform-Specific Guides](docs/installation/)** - Windows, macOS, Linux, VS Code

**Publishing & Distribution:**
- **[TestPyPI Upload Guide](docs/guides/TESTPYPI_UPLOAD_GUIDE.md)** - Upload to TestPyPI for testing
- **[Publishing Guide](docs/guides/PUBLISHING.md)** - Publish to production PyPI

**API Documentation:**
- **[Complete API Reference](docs/functions/README.md)** - All SDK functions
- **[All Guides](docs/guides/README.md)** - Complete guide index

## WebSocket Streaming Example

```python
# Setup callbacks
def on_message(message):
    print(f"Live Data: {message}")

def on_error(error):
    print(f"Error: {error}")

def on_open():
    print("WebSocket Connected")

def on_close():
    print("WebSocket Closed")

# Assign callbacks
client.on_message = on_message
client.on_error = on_error
client.on_open = on_open
client.on_close = on_close

# Subscribe to live feed
client.subscribe(
    instrument_tokens=[
        {'instrument_token': '1333', 'exchange_segment': 'nse_cm'}
    ],
    isIndex=False,
    isDepth=False
)
```

## Exception Handling

```python
from neo_api_client import (
    NeoAPIException,
    AuthenticationError,
    ValidationError,
    RateLimitError,
    NetworkError,
    OrderError
)

try:
    response = client.place_order(...)
except AuthenticationError:
    print("Authentication failed - please login again")
except ValidationError as e:
    print(f"Invalid parameters: {e}")
except RateLimitError:
    print("Rate limit exceeded - please retry after some time")
except OrderError as e:
    print(f"Order placement failed: {e}")
except NeoAPIException as e:
    print(f"API error: {e}")
```

## Environment Setup

Create a `.env` file for credentials:

```bash
NEO_MOBILE_NUMBER=+919876543210
NEO_UCC=YOUR_UCC
NEO_TOTP_SECRET=YOUR_TOTP_SECRET_KEY
NEO_MPIN=123456
```

## Performance Benchmarks

Average API response times (production environment):

| API Function | Avg Latency |
|--------------|-------------|
| Login & Authentication | 134-367 ms |
| Order Operations | 67-71 ms |
| Portfolio & Positions | 68-77 ms |
| Market Data (Quotes) | 289 ms |
| Margin Calculation | 110 ms |
| Scrip Master | 1250 ms |

*Tested on production environment with real API calls*

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

## Architecture

The SDK includes enterprise-grade reliability features:

- **Rate Limiter** - Prevents API throttling
- **Circuit Breaker** - Handles service failures gracefully
- **Retry Logic** - Automatic retry with exponential backoff
- **Structured Logging** - Request/response tracking with correlation IDs
- **Type Safety** - Full mypy type checking support

## Development

### Setup

```bash
# Clone repository
git clone https://github.com/Kotak-Neo/kotak-neo-python.git
cd kotak-neo-python

# Install dependencies
pip install -e ".[dev]"

# Setup pre-commit hooks
pre-commit install
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=neo_api_client --cov-report=html

# Run smoke tests (requires .env configuration)
python tests/e2e/smoke_test.py
```

### Code Quality

```bash
# Format code
ruff format .

# Lint code
ruff check .

# Type checking
mypy neo_api_client

# Security scan
bandit -r neo_api_client
```

## Requirements

- **Python**: 3.10 or higher
- **Core Dependencies**: numpy, pandas, PyJWT, requests, websocket-client, structlog, tenacity

See [pyproject.toml](pyproject.toml) for complete dependency list.

## Repository Structure

```
kotak-neo-python/
├── neo_api_client/          # Main package
│   ├── services/            # API service modules
│   ├── websocket/           # WebSocket implementation
│   ├── utils/               # Utility functions
│   ├── neo_api.py          # Main NeoAPI class
│   ├── exceptions.py       # Exception hierarchy
│   └── ...                 # Core modules
├── tests/                   # Test suite
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   └── e2e/                # End-to-end tests
├── docs/                    # Documentation
│   ├── functions/          # API function docs
│   └── installation/       # Installation guides
└── pyproject.toml          # Project configuration
```

## Support

- **Documentation**: [GitHub Docs](https://github.com/Kotak-Neo/kotak-neo-python/tree/main/docs)
- **Issues**: [GitHub Issues](https://github.com/Kotak-Neo/kotak-neo-python/issues)
- **Email**: support@kotakneo.com

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Disclaimer

This is the official SDK for Kotak Neo Trading APIs. Trading in financial markets involves substantial risk. Users are responsible for their own trading decisions and should thoroughly test their strategies before live trading.

**⚠️ Risk Warning**: As per SEBI study, 9 out of 10 individual traders in equity F&O segment incur net losses. Please trade responsibly.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and updates.

---

**Version**: 2.1.1  
**Status**: Production/Stable  
**Built with ❤️ by Kotak Neo Team**
