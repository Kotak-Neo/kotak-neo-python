# Installation Guide

Complete installation guides for kotakneoapi SDK across different platforms and IDEs.

> **⚠️ Important:** The package is currently in development and not yet published to PyPI.  
> For installation instructions, see **[Local Installation Guide](./local-install.md)**

## 📚 Installation Guides by Platform

> **📖 Complete Reference:** See [Installation Reference Guide](../guides/INSTALLATION_REFERENCE.md) for comprehensive guide to all installation methods and platform-specific guides.

### Current Method (Development)
- **[Local Installation](local-install.md)** - Install from source repository ⭐ **START HERE**

### Operating Systems
- **[Windows](windows.md)** - Complete guide for Windows 10/11 with Visual Studio Code
- **[macOS](macos.md)** - Installation on macOS with Homebrew and VS Code
- **[Linux](linux.md)** - Ubuntu/Debian, CentOS/RHEL, and Arch Linux

### IDEs & Editors
- **[Visual Studio Code](vscode.md)** - Cross-platform VS Code setup
- **[PyCharm](pycharm.md)** - JetBrains PyCharm Professional/Community
- **[Jupyter Notebook](jupyter.md)** - Interactive development with Jupyter
- **[Terminal/CLI](cli.md)** - Command-line only setup

## 🚀 Quick Start (Any Platform)

### Prerequisites

**Before Installation:**
1. **Get Consumer Key (REQUIRED)**
   - Login to Kotak NEO app/web
   - Go to **Invest** tab → **Trade API** card
   - Click **Generate application**
   - Copy the token (needed for authentication)

**System Requirements:**
- Python 3.10 or higher
- pip (Python package manager)
- Virtual environment support

### Basic Installation

```bash
# Create virtual environment
python -m venv venv

# Activate it (varies by platform)
# Linux/macOS: source venv/bin/activate
# Windows (PowerShell): .\venv\Scripts\Activate.ps1
# Windows (cmd): .\venv\Scripts\activate.bat

# Install SDK
pip install kotakneoapi

# Verify installation
python -c "from neo_api_client import NeoAPI; print('✓ Installation successful')"
```

## 📦 Installation Methods

### Method 1: From PyPI (Recommended)
```bash
pip install kotakneoapi
```

### Method 2: From GitHub
```bash
pip install git+https://github.com/Kotak-Neo/kotak-neo-python.git
```

### Method 3: From Source (Development)
```bash
git clone https://github.com/Kotak-Neo/kotak-neo-python.git
cd kotak-neo-python
pip install -e ".[dev]"
```

## 🔧 Platform-Specific Quick Links

### Windows Users
1. [Install Python](windows.md#1-install-python)
2. [Install VS Code](windows.md#2-install-visual-studio-code)
3. [Create Virtual Environment](windows.md#step-2-create-virtual-environment)
4. [Install SDK](windows.md#step-3-install-the-sdk)

### macOS Users
1. [Install Homebrew](macos.md#1-install-homebrew)
2. [Install Python](macos.md#2-install-python)
3. [Install VS Code](macos.md#3-install-visual-studio-code)
4. [Install SDK](macos.md#installation-methods)

### Linux Users
1. [Install Python](linux.md#ubuntu-debian)
2. [Create Virtual Environment](linux.md#create-virtual-environment)
3. [Install SDK](linux.md#install-the-sdk)

## 🎓 Learning Path

**New to Python?**
1. Start with [Windows Guide](windows.md) or [macOS Guide](macos.md)
2. Follow the [Visual Studio Code Setup](vscode.md)
3. Try the sample project in each guide

**Experienced Developer?**
1. Quick install: `pip install kotakneoapi`
2. Check [CLI Setup](cli.md) for minimal setup
3. See [Development Setup](#development-setup-for-contributors) below

## 🧪 Development Setup (For Contributors)

```bash
# Clone repository
git clone https://github.com/Kotak-Neo/kotak-neo-python.git
cd kotak-neo-python

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or appropriate command for your platform

# Install with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Check coverage
pytest --cov=neo_api_client --cov-report=html
```

## 📋 System Requirements

### Minimum Requirements
- **Python:** 3.10 or higher
- **pip:** 20.0 or higher
- **RAM:** 512 MB minimum
- **Disk Space:** 100 MB for SDK + dependencies
- **Internet:** Required for installation and API calls

### Recommended Requirements
- **Python:** 3.12 or higher
- **pip:** Latest version
- **RAM:** 2 GB or more
- **Disk Space:** 500 MB (for dev dependencies and testing)
- **IDE:** VS Code, PyCharm, or Jupyter

## 🔑 Setup Credentials

After installation, configure your API credentials:

### Step 1: Create .env file
```bash
cp .env.example .env
nano .env  # or use your preferred editor
```

### Step 2: Add Required Credentials
```bash
# REQUIRED - Consumer Key from NEO app Trade API
NEO_CONSUMER_KEY=your-token-here

# Your registered mobile with country code
NEO_MOBILE_NUMBER=+919876543210

# Your UCC from NEO app Profile
NEO_UCC=ABC123

# TOTP secret from QR code during TOTP registration
NEO_TOTP_SECRET=your-base32-secret

# Your trading MPIN
NEO_MPIN=123456
```

### How to Get Each Credential:

**NEO_CONSUMER_KEY** (REQUIRED)
1. Login to Kotak NEO app/web
2. Go to **Invest** → **Trade API**
3. Click **Generate application**
4. Copy the token

**NEO_UCC**
- Find in NEO app under **Profile** section

**NEO_TOTP_SECRET**
1. Visit https://www.kotaksecurities.com/platform/kotak-neo-trade-api/
2. Register for TOTP
3. Scan QR code with authenticator app
4. Save the base32 secret key (not the 6-digit code)

## 🔍 Verification Steps

After installation and credentials setup:

```python
# test_install.py
from neo_api_client import NeoAPI, __version__

print(f"✓ kotakneoapi version: {__version__}")

# Create client instance with your consumer_key
client = NeoAPI(
    consumer_key="your-consumer-key",  # REQUIRED
    environment="prod"
)

print("✓ NeoAPI client created successfully")
print("✓ Installation verified!")
```

Run with:
```bash
python test_install.py
```

## 🐛 Common Issues

### Issue: "python command not found"
**Solution:** Python not in PATH. See platform-specific guides for PATH setup.

### Issue: "pip command not found"
**Solution:**
```bash
python -m ensurepip --upgrade
python -m pip install --upgrade pip
```

### Issue: "Permission denied"
**Solution:** Use virtual environment (recommended) or:
```bash
pip install --user kotakneoapi  # Not recommended
```

### Issue: SSL/Certificate errors
**Solution:**
```bash
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org kotakneoapi
```

### Issue: Virtual environment not activating
**Solution:** See platform-specific activation commands in guides.

## 📚 Additional Resources

### Documentation
- [Main README](../../README.md)
- [API Documentation](../functions/README.md)
- [All Guides](../guides/README.md)
- [Publishing Guide](../guides/PUBLISHING.md)

### Platform-Specific
- [Windows Installation](windows.md)
- [macOS Installation](macos.md)
- [Linux Installation](linux.md)

### IDE Setup
- [VS Code Setup](vscode.md)
- [PyCharm Setup](pycharm.md)
- [Jupyter Setup](jupyter.md)

### External Links
- [Python Downloads](https://www.python.org/downloads/)
- [pip Documentation](https://pip.pypa.io/)
- [Virtual Environments](https://docs.python.org/3/library/venv.html)
- [Kotak Neo API Docs](https://developers.kotaksecurities.com/)

## 💬 Getting Help

**Found an issue with installation?**
- Check the [Troubleshooting](#-common-issues) section
- Review platform-specific guide
- Open an issue: https://github.com/Kotak-Neo/kotak-neo-python/issues

**Need support?**
- Email: support@kotakneo.com
- GitHub Issues: https://github.com/Kotak-Neo/kotak-neo-python/issues

## 🔄 Updating the SDK

```bash
# Activate your virtual environment first
pip install --upgrade kotakneoapi

# Check new version
pip show kotakneoapi
```

## 🗑️ Uninstalling

```bash
# Activate your virtual environment first
pip uninstall kotakneoapi

# Confirm with 'y'
```

---

**Next Steps:**
1. Choose your platform guide from the list above
2. Follow the installation steps
3. Set up your credentials in `.env` file
4. Run your first trading bot!
