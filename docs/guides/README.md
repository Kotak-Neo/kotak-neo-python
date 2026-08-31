# Guides

Comprehensive guides for developers, maintainers, and contributors.

## 📚 Available Guides

### For Developers

#### [Migration Guide (v2.0.2 → v3.0.X)](MIGRATION.md) ⭐ **UPGRADING? START HERE**
Step-by-step guide for upgrading from the previous SDK version.

**Topics Covered:**
- Automated migration scanner (`docs/scripts/migrate_from_v2.py`)
- Authentication (`consumer_key` + TOTP) confirmation
- Stricter order validation (product `CNC`/`NRML`/`MIS`/`MTF`, per-segment validity)
- Error handling: exceptions instead of silent `{"Error": ...}` dicts
- Removed methods (legacy WebSocket, cover/bracket cancel)
- WebSocket migration: callbacks → async/await with typed messages
- Upgrade checklist

**Who should read:**
- Anyone upgrading existing code from v2.0.2

---

#### [SFeed WebSocket Guide](websocket.md)
Modern async/await streaming client for live market data (v3.0.0+).

**Topics Covered:**
- Async/await usage with `async for` iteration
- Batched subscribe/unsubscribe and snapshot
- Typed messages (`SFeedScrip`, `SFeedScripLite`, `SFeedIndex`, `SFeedMarketStatus`)
- Configuration, error handling, and callbacks
- Migration from the legacy callback-based WebSocket (removed in v3.0.X)

**Who should read:**
- Anyone consuming real-time market data
- Developers migrating from the pre-2.0.2 WebSocket API

---

#### [Sync/Multi-Process Integration Guide](sync-integration.md)
Production pattern for consuming the async SFeed/order-feed clients from a
synchronous, multi-process app (gunicorn/uWSGI sync workers, Celery).

**Topics Covered:**
- Background-thread + thread-safe-queue bridge for the async clients
- gunicorn (`post_fork`) and Celery (`worker_process_init`) wiring
- Fork-safety and one-connection-per-process considerations

**Who should read:**
- Anyone running Django/Flask behind sync workers, or Celery, that needs
  live market data without becoming asyncio-native

---

#### [Logging Guide](logging.md)
`setup_logging()`, log levels, and configuration for REST and WebSocket clients.

**Topics Covered:**
- `setup_logging(...)` usage (console/file levels, `"NOLOG"`)
- Rotating log file and its environment variables
- Log levels used by the SDK (`INFO`/`WARNING`/`ERROR`) and what's logged at each
- Automatic masking of sensitive fields, and the `environment` field

**Who should read:**
- Anyone monitoring REST/WebSocket traffic or troubleshooting connectivity

---

## Quick Links

### Installation & Setup
- **[Installation Overview](../installation/README.md)** - All installation options
- **[Local Installation](../installation/local-install.md)** - Current method (dev)
- **[Windows Guide](../installation/windows.md)** - Windows 10/11
- **[macOS Guide](../installation/macos.md)** - macOS with Homebrew
- **[Linux Guide](../installation/linux.md)** - Ubuntu/CentOS/Arch
- **[VS Code Setup](../installation/vscode.md)** - IDE configuration

### Upgrading
- **[Migration Guide (v2.0.2 → v3.0.X)](MIGRATION.md)** - Upgrade existing code
- **[Migration Scanner](../scripts/migrate_from_v2.py)** - Automated script that flags v2-only calls in your code

### API Documentation
- **[API Functions](../functions/README.md)** - Complete API reference
- **[Authentication](../functions/authentication/)** - Login & auth
- **[Orders](../functions/orders/)** - Order management
- **[Portfolio](../functions/portfolio/)** - Holdings & positions
- **[Market Data](../functions/market_data/)** - Quotes & scrips
- **[WebSocket](../functions/websocket/)** - Real-time streaming
- **[SFeed WebSocket Guide](websocket.md)** - Async streaming client & migration

---

## Guide Selection Tool

### I want to...

**...install the SDK**
→ [Installation Overview](../installation/README.md)

**...set up my development environment**
→ [Local Installation Guide](../installation/local-install.md)

**...upgrade from an older version (v2.0.2)**
→ [Migration Guide](MIGRATION.md), then run the [migration scanner](../scripts/migrate_from_v2.py) against your code

**...learn the API**
→ [API Functions Documentation](../functions/README.md)

**...troubleshoot installation**
→ [Installation Overview - Common Issues](../installation/README.md#-common-issues)

---

## Documentation Structure

```
docs/
├── guides/                          # 📖 You are here
│   ├── README.md                    # This file
│   ├── MIGRATION.md                 # v2.0.2 → v3.0.X upgrade guide
│   ├── websocket.md                 # Async SFeed WebSocket guide
│   ├── sync-integration.md          # Sync/multi-process bridge for the async feeds
│   └── logging.md                   # setup_logging(), log levels & configuration
│
├── installation/                    # Platform-specific guides
│   ├── README.md
│   ├── local-install.md
│   ├── windows.md
│   ├── macos.md
│   ├── linux.md
│   └── vscode.md
│
├── scripts/                         # Standalone helper scripts
│   └── migrate_from_v2.py           # v2 -> v3.0.X migration scanner (read-only)
│
└── functions/                       # API documentation
    ├── README.md
    ├── authentication/
    ├── orders/
    ├── portfolio/
    ├── market_data/
    └── websocket/
```

---

## Contributing

Found an issue or want to improve a guide?

1. Check [GitHub Issues](https://github.com/Kotak-Neo/kotak-neo-python/issues)
2. Submit a pull request with improvements
3. Follow the documentation style guide

---

## Support

**Need help?**
- 📧 Email: support@kotakneo.com
- 🐛 GitHub Issues: https://github.com/Kotak-Neo/kotak-neo-python/issues
- 📖 Main README: [../../README.md](../../README.md)

---

## Recent Updates

- **2026-08-19**: Added standalone [Logging Guide](logging.md); logging content moved out of the Migration Guide and WebSocket Guide
- **2026-08-03**: Added automated migration scanner (`docs/scripts/migrate_from_v2.py`); removed the redundant/stale Installation Reference Guide (see [docs/installation/](../installation/README.md) instead)
- **2026-07-01**: Added SFeed WebSocket Guide; legacy callback WebSocket removed in v2.2.0
- **2026-06-25**: Organized guides into dedicated folder

---

[[Back to Main README]](../../README.md) | [[Installation Guides]](../installation/README.md) | [[API Documentation]](../functions/README.md)
