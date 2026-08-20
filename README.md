# Kotak Neo API - Python SDK

Official Python SDK for Kotak Neo Trading APIs - a modern, well-tested trading client for the Kotak Neo platform.

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![PyPI Version](https://img.shields.io/badge/pypi-v3.0.1-green.svg)](https://pypi.org/project/kotakneoapi/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/Kotak-Neo/kotak-neo-python/blob/main/LICENSE)

> **This is the actively maintained Python SDK**, superseding
> [`kotak-neo-api-v2`](https://github.com/Kotak-Neo/kotak-neo-api-v2) (now legacy).
> Already on `kotak-neo-api-v2`? See the
> **[Migration Guide](https://github.com/Kotak-Neo/kotak-neo-python/blob/main/docs/guides/MIGRATION.md)**.

## Features

✅ **Authentication** - TOTP-based secure login with 2FA  
✅ **Order Management** - Place, modify, cancel orders (Regular/AMO)  
✅ **Portfolio & Positions** - Real-time holdings, positions, and limits  
✅ **Market Data** - Live quotes, scrip master, search functionality  
✅ **SFeed WebSocket Streaming** - Modern async/await live market feed with typed messages, enriched with `trading_symbol`  
✅ **HTTP/2 Transport** - REST calls use HTTP/2 (via httpx) with automatic HTTP/1.1 fallback  
✅ **Optional Reliability Utilities** - Opt-in rate limiting, plus retry and circuit-breaker helpers  
✅ **Enhanced Logging** - Rotating log file with REST/WebSocket tracking and automatic masking of sensitive data  
✅ **Comprehensive Error Handling** - Detailed exception hierarchy with input validation  
✅ **Type Safety** - Full mypy type checking support  
✅ **Extensive Testing** - 100% test coverage (unit, integration, and E2E tests)  

## Installation

### From PyPI

```bash
pip install kotakneoapi
```

### For Development (Local Installation)

```bash
# Clone the repository
git clone https://github.com/Kotak-Neo/kotak-neo-python.git
cd kotak-neo-python

# Install in development/editable mode
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

## Quick Start

### Prerequisites

1. **Get Consumer Key (REQUIRED)**: Login to Kotak NEO app/web → **More** tab → **Trade API** card → Generate application → Copy the token
   - This token is used in the Authorization header for all API requests
   - Authentication will fail without this token
2. **Register for TOTP**: Visit API Dashboard (Neo App/Web → more tab → trade API), on top right menu bar click "TOTP Registration" → Register for TOTP → Scan QR code with authenticator app (Google Authenticator, Authy, etc.)

### Getting started with quick order placement

```python
from neo_api_client import NeoAPI

# Initialize the client
client = NeoAPI(
    consumer_key="your-consumer-key-token",  # Token from NEO app Trade API card
    environment="prod",  # production (default)
    access_token=None,  # Optional
    neo_fin_key=None,  # Optional
)

# Step 1: Login with TOTP
login_response = client.totp_login(
    mobile_number="+919876543210",  # Your registered mobile with country code
    ucc="YOUR_UCC",  # Find in NEO app/web under Profile section
    totp="123456",  # 6-digit code from authenticator app (changes every 30 seconds)
)

# Step 2: Validate with MPIN to complete authentication
validate_response = client.totp_validate(mpin="123456")  # Your trading MPIN

# Place an order
order_response = client.place_order(
    exchange_segment="nse_cm",
    product="CNC",
    price="1500.00",
    order_type="L",
    quantity="10",
    validity="DAY",
    trading_symbol="RELIANCE-EQ",
    transaction_type="B",
)

# Get real-time quotes
quotes = client.quotes(
    instrument_tokens=[{"instrument_token": "1333", "exchange_segment": "nse_cm"}], quote_type="all"
)

# Logout
client.logout()
```

## Documentation

### 📚 [Complete API Documentation](https://github.com/Kotak-Neo/kotak-neo-python/blob/main/docs/functions/README.md)

Detailed documentation for all SDK functions with examples and real API responses.

#### Quick Links

**Authentication**
- [TOTP Login](https://github.com/Kotak-Neo/kotak-neo-python/blob/main/docs/functions/authentication/totp_login.md) | [TOTP Validate](https://github.com/Kotak-Neo/kotak-neo-python/blob/main/docs/functions/authentication/totp_validate.md) | [What's My IP](https://github.com/Kotak-Neo/kotak-neo-python/blob/main/docs/functions/authentication/whatsmyip.md) | [Logout](https://github.com/Kotak-Neo/kotak-neo-python/blob/main/docs/functions/authentication/logout.md)

**Order Management**
- [Place Order](https://github.com/Kotak-Neo/kotak-neo-python/blob/main/docs/functions/orders/place_order.md) | [Modify Order](https://github.com/Kotak-Neo/kotak-neo-python/blob/main/docs/functions/orders/modify_order.md) | [Cancel Order](https://github.com/Kotak-Neo/kotak-neo-python/blob/main/docs/functions/orders/cancel_order.md)
- [Order Report](https://github.com/Kotak-Neo/kotak-neo-python/blob/main/docs/functions/orders/order_report.md) | [Order History](https://github.com/Kotak-Neo/kotak-neo-python/blob/main/docs/functions/orders/order_history.md) | [Trade Report](https://github.com/Kotak-Neo/kotak-neo-python/blob/main/docs/functions/orders/trade_report.md)

**Portfolio & Positions**
- [Holdings](https://github.com/Kotak-Neo/kotak-neo-python/blob/main/docs/functions/portfolio/holdings.md) | [Positions](https://github.com/Kotak-Neo/kotak-neo-python/blob/main/docs/functions/portfolio/positions.md)
- [Limits](https://github.com/Kotak-Neo/kotak-neo-python/blob/main/docs/functions/portfolio/limits.md) | [Margin Required](https://github.com/Kotak-Neo/kotak-neo-python/blob/main/docs/functions/portfolio/margin_required.md)

**Market Data**
- [Quotes](https://github.com/Kotak-Neo/kotak-neo-python/blob/main/docs/functions/market_data/quotes.md) | [Scrip Master](https://github.com/Kotak-Neo/kotak-neo-python/blob/main/docs/functions/market_data/scrip_master.md) | [Search Scrip](https://github.com/Kotak-Neo/kotak-neo-python/blob/main/docs/functions/market_data/search_scrip.md)

**WebSocket**
- Market data (SFeed): [Market Feed (Subscribe/Unsubscribe)](https://github.com/Kotak-Neo/kotak-neo-python/blob/main/docs/functions/websocket/market_feed.md)
- Order & positions: [Order Feed](https://github.com/Kotak-Neo/kotak-neo-python/blob/main/docs/functions/websocket/order_feed.md)
- Full guide: [SFeed WebSocket](https://github.com/Kotak-Neo/kotak-neo-python/blob/main/docs/guides/websocket.md)

### 📖 Guides & Documentation

**Upgrading:**
- **[Migration Guide (v2.0.2 → v3.0.X)](https://github.com/Kotak-Neo/kotak-neo-python/blob/main/docs/guides/MIGRATION.md)** - Upgrade existing code to the latest version
- **[Migration Scanner](https://github.com/Kotak-Neo/kotak-neo-python/blob/main/docs/scripts/migrate_from_v2.py)** - Run against your project to auto-detect v2-only calls before you start migrating by hand

**Installation:**
- **[Installation Overview](https://github.com/Kotak-Neo/kotak-neo-python/blob/main/docs/installation/README.md)** - All installation options
- **[Local Installation](https://github.com/Kotak-Neo/kotak-neo-python/blob/main/docs/installation/local-install.md)** - Install from source (for contributors)
- **[Platform-Specific Guides](https://github.com/Kotak-Neo/kotak-neo-python/tree/main/docs/installation)** - Windows, macOS, Linux, VS Code

**API Documentation:**
- **[Complete API Reference](https://github.com/Kotak-Neo/kotak-neo-python/blob/main/docs/functions/README.md)** - All SDK functions
- **[SFeed WebSocket Guide](https://github.com/Kotak-Neo/kotak-neo-python/blob/main/docs/guides/websocket.md)** - Async streaming client, protocol & migration
- **[Logging Guide](https://github.com/Kotak-Neo/kotak-neo-python/blob/main/docs/guides/logging.md)** - `setup_logging()`, log levels & configuration
- **[All Guides](https://github.com/Kotak-Neo/kotak-neo-python/blob/main/docs/guides/README.md)** - Complete guide index

## WebSocket Streaming Example (SFeed)

Live market data is delivered through the modern async/await **SFeed** WebSocket
client. It uses `async for` iteration and returns type-safe Pydantic messages,
each enriched with its `trading_symbol` (resolved from the subscribe ack).

```python
import asyncio
from neo_api_client import NeoAPI
from neo_api_client.websocket.feed import WsToken, SFeedScrip


async def main():
    client = NeoAPI(consumer_key="your-consumer-key-token", environment="prod")
    client.totp_login(mobile_number="+919876543210", ucc="YOUR_UCC", totp="123456")
    client.totp_validate(mpin="123456")

    # create_websocket() builds a SFeedWebSocket from the current session
    async with client.create_websocket() as ws:
        # Batch-subscribe any number of instruments in a single call
        await ws.subscribe_scrips([
            WsToken("nse_cm", "Nifty 50"),
            WsToken("nse_cm", "11536"),
        ])

        async for message in ws:
            if isinstance(message, SFeedScrip):
                print(
                    f"{message.trading_symbol} ({message.instrument_token}) "
                    f"LTP: {message.last_traded_price}"
                )


asyncio.run(main())
```

> **Note:** The SFeed client works out of the box — its dependencies
> (`websockets`, `pydantic`) ship with the base install. The legacy callback-based
> WebSocket (`client.subscribe(...)`, `on_message`, etc.) was **removed in v2.2.0** —
> see the [SFeed WebSocket guide](https://github.com/Kotak-Neo/kotak-neo-python/blob/main/docs/guides/websocket.md) for the full API and a
> migration reference.

## Order & Position Streaming Example

Order-lifecycle events and live position updates stream over a separate
async/await WebSocket, `create_order_feed()`. It returns type-safe `OrderUpdate` /
`PositionUpdate` messages.

```python
import asyncio
from neo_api_client import NeoAPI
from neo_api_client.websocket.orderfeed import OrderUpdate, PositionUpdate, OrderStatus


async def main():
    client = NeoAPI(consumer_key="your-consumer-key-token", environment="prod")
    client.totp_login(mobile_number="+919876543210", ucc="YOUR_UCC", totp="123456")
    client.totp_validate(mpin="123456")

    # create_order_feed() connects to wss://<baseurl>/realtime using the session
    async with client.create_order_feed() as feed:
        async for message in feed:
            if isinstance(message, OrderUpdate):
                print(f"order {message.data.order_no} -> {message.data.order_status}")
            elif isinstance(message, PositionUpdate):
                print(f"position {message.data.symbol}")


asyncio.run(main())
```

> Full reference: [Order & Position Feed](https://github.com/Kotak-Neo/kotak-neo-python/blob/main/docs/functions/websocket/order_feed.md).

## Exception Handling

```python
from neo_api_client import (
    NeoAPIException,
    AuthenticationError,
    ValidationError,
    RateLimitError,
    NetworkError,
    OrderError,
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

Create a `.env` file for credentials (copy from `.env.example`):

```bash
# Consumer Key from NEO app (REQUIRED - Used in Authorization header)
# Get it: NEO app → More → Trade API → Generate application → Copy token
NEO_CONSUMER_KEY=your-consumer-key-token

# Your registered mobile number with country code
NEO_MOBILE_NUMBER=+919876543210

# Your UCC (User Client Code) from NEO app Profile section
NEO_UCC=YOUR_UCC

# TOTP secret key (base32 string from QR code during TOTP registration)
# This is NOT the 6-digit code - it's the secret key from authenticator setup
NEO_TOTP_SECRET=YOUR_TOTP_SECRET_KEY

# Your trading MPIN
NEO_MPIN=123456
```

**How to get credentials:**
- **Consumer Key**: NEO app → More → Trade API → Generate application → Copy token
- **UCC**: NEO app → Profile section
- **TOTP Secret**: https://www.kotakneo.com/platform/kotak-neo-trade-api/ → Register for TOTP → Note the secret from QR code setup



## Common Parameters

### Exchange Segments
- `nse_cm` - NSE Cash Market
- `bse_cm` - BSE Cash Market
- `nse_fo` - NSE Futures & Options
- `bse_fo` - BSE Futures & Options
- `mcx_fo` - MCX Commodities
- `cde_fo` - Currency Derivatives (market data/quotes only — **not** accepted by `place_order`/`margin_required`, which don't support this segment)

### Product Types
- `CNC` - Cash & Carry (Delivery)
- `MIS` - Margin Intraday Square-off
- `NRML` - Normal (Carry Forward)
- `MTF` - Margin Trading Facility

Note: `place_order`/`modify_order` only accept these four exact codes (Bracket
and Cover orders are no longer supported).

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

Always on for every request:

- **HTTP/2 Transport** - REST calls run over HTTP/2 (via `httpx`) with connection pooling and automatic HTTP/1.1 fallback
- **Structured Logging** - Request/response tracking with correlation IDs
- **Type Safety** - Full mypy type checking support

Optional reliability utilities (shipped, tested, and importable, but **not wired
into the request path by default** — you opt in):

- **Rate Limiter** - Token-bucket throttling (per second/minute/hour) to avoid tripping API quotas. Enable with `RESTClientObject(..., enable_rate_limiting=True)`.
- **Retry Logic** - Exponential backoff with jitter for transient errors, via the `with_retry` / `create_retry_decorator` decorators in `neo_api_client.retry`.
- **Circuit Breaker** - `CircuitBreaker` in `neo_api_client.circuit_breaker` to stop calling a failing service and let it recover.

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

> **SDK contributors:** the smoke/integration test runners can target an internal
> environment via the `NEO_ENVIRONMENT` variable. Ask an internal maintainer for
> the dev `.env` template for that setup. This is not needed by normal SDK users —
> the client always uses production by default.

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
- **Core Dependencies**: numpy, pandas, PyJWT, httpx[http2], websocket-client, structlog, tenacity, python-decouple, pyotp, websockets, pydantic

See [pyproject.toml](https://github.com/Kotak-Neo/kotak-neo-python/blob/main/pyproject.toml) for complete dependency list.

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

Reporting a bug? Enable file logging with `setup_logging(file_level="INFO")` (see the
[Logging Guide](https://github.com/Kotak-Neo/kotak-neo-python/blob/main/docs/guides/logging.md)),
reproduce the issue, and attach the resulting `logs/neo-api-client.log` to your issue —
sensitive fields are already masked, so it's safe to share as-is.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License - see [LICENSE](https://github.com/Kotak-Neo/kotak-neo-python/blob/main/LICENSE) file for details.

## Disclaimer

This is the official SDK for Kotak Neo Trading APIs. Trading in financial markets involves substantial risk. Users are responsible for their own trading decisions and should thoroughly test their strategies before live trading.

**⚠️ Risk Warning**: As per SEBI study, 9 out of 10 individual traders in equity F&O segment incur net losses. Please trade responsibly.

## Changelog

See [CHANGELOG.md](https://github.com/Kotak-Neo/kotak-neo-python/releases) for version history and updates.

---

**Version**: 3.0.1  
**Status**: Production/Stable  
**Built with ❤️ by Kotak Neo Team**
