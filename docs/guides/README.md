# Guides

Comprehensive guides for developers, maintainers, and contributors.

## 📚 Available Guides

### For Developers

#### [Migration Guide (v2.0.2 → v2.3.0)](MIGRATION.md) ⭐ **UPGRADING? START HERE**
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
Modern async/await streaming client for live market data (v2.2.0+).

**Topics Covered:**
- Async/await usage with `async for` iteration
- Batched subscribe/unsubscribe and snapshot
- Typed messages (`SFeedScrip`, `SFeedScripLite`, `SFeedIndex`, `SFeedMarketStatus`)
- Configuration, error handling, and callbacks
- Migration from the legacy callback-based WebSocket (removed in v2.2.0)

**Who should read:**
- Anyone consuming real-time market data
- Developers migrating from the pre-2.2.0 WebSocket API

---

#### [Installation Reference Guide](INSTALLATION_REFERENCE.md)
Complete reference for installing the Kotak Neo Python SDK across different platforms.

**Topics Covered:**
- Platform-specific installation (Windows, macOS, Linux)
- IDE setup (VS Code, PyCharm, Jupyter)
- Installation decision tree
- Quick reference matrix
- Troubleshooting by platform

**Who should read:**
- New users choosing installation method
- Developers setting up development environment
- Contributors preparing for development
- System administrators deploying to servers

---

### For Maintainers & Publishers

#### [TestPyPI Upload Guide](TESTPYPI_UPLOAD_GUIDE.md) ⭐ **START HERE**
Step-by-step guide for uploading your package to TestPyPI for testing before production release.

**Topics Covered:**
- Building package distributions
- Getting TestPyPI API tokens
- Uploading to TestPyPI
- Testing installation
- Troubleshooting common issues
- Security best practices

**Who should read:**
- First-time publishers
- Maintainers preparing for release
- Anyone wanting to test package distribution

**Current Status:**
✅ Package built and validated, ready to upload!

---

#### [Publishing Guide](PUBLISHING.md)
Complete guide for building and publishing the package to PyPI (production).

**Topics Covered:**
- Pre-publication checklist
- Building distribution files
- TestPyPI testing workflow
- Production PyPI publishing
- Version management
- CI/CD automation
- Security best practices
- Post-publication steps

**Who should read:**
- Package maintainers
- Release managers
- Contributors preparing releases
- DevOps engineers setting up CI/CD

---

## Quick Links

### Installation & Setup
- **[Installation Reference](INSTALLATION_REFERENCE.md)** - Complete platform guide
- **[Local Installation](../installation/local-install.md)** - Current method (dev)
- **[Windows Guide](../installation/windows.md)** - Windows 10/11
- **[macOS Guide](../installation/macos.md)** - macOS with Homebrew
- **[Linux Guide](../installation/linux.md)** - Ubuntu/CentOS/Arch
- **[VS Code Setup](../installation/vscode.md)** - IDE configuration

### Publishing & Distribution
- **[TestPyPI Upload](TESTPYPI_UPLOAD_GUIDE.md)** - Testing release (current)
- **[Publishing Guide](PUBLISHING.md)** - Production release
- **[PyPI Best Practices](PUBLISHING.md#security-best-practices)** - Security guidelines

### Upgrading
- **[Migration Guide (v2.0.2 → v2.3.0)](MIGRATION.md)** - Upgrade existing code
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
→ [Installation Reference Guide](INSTALLATION_REFERENCE.md)

**...set up my development environment**
→ [Local Installation Guide](../installation/local-install.md)

**...publish to TestPyPI (testing)**
→ [TestPyPI Upload Guide](TESTPYPI_UPLOAD_GUIDE.md)

**...publish to production PyPI**
→ [Publishing Guide](PUBLISHING.md)

**...upgrade from an older version (v2.0.2)**
→ [Migration Guide](MIGRATION.md), then run the [migration scanner](../scripts/migrate_from_v2.py) against your code

**...learn the API**
→ [API Functions Documentation](../functions/README.md)

**...troubleshoot installation**
→ [Installation Reference - Troubleshooting](INSTALLATION_REFERENCE.md#troubleshooting-guides)

---

## Documentation Structure

```
docs/
├── guides/                          # 📖 You are here
│   ├── README.md                    # This file
│   ├── MIGRATION.md                 # v2.0.2 → v2.3.0 upgrade guide
│   ├── websocket.md         # Async SFeed WebSocket guide
│   ├── INSTALLATION_REFERENCE.md    # Complete installation guide
│   ├── TESTPYPI_UPLOAD_GUIDE.md    # TestPyPI publishing
│   └── PUBLISHING.md                # PyPI publishing
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
│   └── migrate_from_v2.py           # v2 -> v2.3.0 migration scanner (read-only)
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

- **2026-08-03**: Added automated migration scanner (`docs/scripts/migrate_from_v2.py`)
- **2026-07-01**: Added SFeed WebSocket Guide; legacy callback WebSocket removed in v2.2.0
- **2026-06-26**: Added TestPyPI Upload Guide
- **2026-06-25**: Created Installation Reference Guide
- **2026-06-25**: Created Publishing Guide
- **2026-06-25**: Organized guides into dedicated folder

---

[[Back to Main README]](../../README.md) | [[Installation Guides]](../installation/README.md) | [[API Documentation]](../functions/README.md)
