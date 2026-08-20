# Local Installation Guide

This guide explains how to install the Kotak Neo Python SDK locally for development or when the package is not yet published to PyPI.

## Prerequisites

- **Python**: 3.10 or higher
- **pip**: Latest version recommended
- **git**: For cloning the repository

### Check Your Python Version

```bash
python --version
# Should show Python 3.10.x or higher
```

### Check pip Version

```bash
pip --version
```

## Installation Methods

### Method 1: Editable/Development Install (Recommended for Development)

This method creates a symbolic link to your local repository, so changes to the code are immediately reflected without reinstalling.

```bash
# 1. Clone the repository
git clone https://github.com/Kotak-Neo/kotak-neo-python.git
cd kotak-neo-python

# 2. Install in editable mode
pip install -e .

# 3. Verify installation
python -c "from neo_api_client import NeoAPI; print('✅ Package installed successfully')"
```

**Advantages:**
- Changes to code are immediately available
- Useful for development and testing
- No need to reinstall after code changes

### Method 2: Install with Development Dependencies

If you plan to contribute or run tests:

```bash
# Clone and navigate to repository
git clone https://github.com/Kotak-Neo/kotak-neo-python.git
cd kotak-neo-python

# Install with all development dependencies
pip install -e ".[dev]"

# This installs additional packages:
# - pytest, pytest-cov (testing)
# - ruff, mypy (code quality)
# - bandit, safety (security)
# - pre-commit (git hooks)
# - pyotp (for smoke tests)
```

### Method 3: Standard Install from Local Directory

For production-like installation without editable mode:

```bash
# Clone the repository
git clone https://github.com/Kotak-Neo/kotak-neo-python.git
cd kotak-neo-python

# Standard install
pip install .
```

### Method 4: Install from Local Wheel

Build and install from a wheel file:

```bash
# Navigate to repository
cd kotak-neo-python

# Install build tools
pip install build

# Build the package
python -m build

# Install from the generated wheel (check dist/ for the actual filename/version)
pip install dist/kotakneoapi-*-py3-none-any.whl
```

## Virtual Environment (Recommended)

Always use a virtual environment to avoid conflicts:

### Using venv

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

# Install the package
pip install -e .
```

### Using conda

```bash
# Create conda environment
conda create -n kotakneo python=3.12

# Activate it
conda activate kotakneo

# Install the package
pip install -e .
```

## Verify Installation

After installation, verify everything works:

```bash
# Test import
python -c "from neo_api_client import NeoAPI; print('✅ Import successful')"

# Check installed version
pip show kotakneoapi

# Check package location
python -c "import neo_api_client; print(neo_api_client.__file__)"
```

## Troubleshooting

### Error: "Could not find a version that satisfies the requirement kotakneoapi"

This error occurs when trying to install from PyPI before the package is published.

**Solution:** Install locally using one of the methods above.

### Error: "No module named 'neo_api_client'"

**Possible causes:**
1. Package not installed
2. Wrong virtual environment activated
3. Import from wrong directory

**Solution:**
```bash
# Reinstall
pip install -e .

# Verify installation
pip list | grep kotakneoapi
```

### Error: "Permission denied"

**Solution:** Use `--user` flag or activate virtual environment:
```bash
pip install --user -e .
```

### Dependency Conflicts

If you encounter dependency conflicts:

```bash
# Create fresh virtual environment
python -m venv fresh_env
source fresh_env/bin/activate  # or fresh_env\Scripts\activate on Windows

# Install in fresh environment
pip install -e .
```

## Updating the Package

### For Editable Install

Changes are automatically reflected. Just pull latest code:

```bash
cd kotak-neo-python
git pull origin main
```

### For Standard Install

Reinstall after pulling updates:

```bash
cd kotak-neo-python
git pull origin main
pip install --upgrade --force-reinstall .
```

## Uninstalling

```bash
pip uninstall kotakneoapi
```

## Environment Setup

After installation, set up your credentials:

```bash
# Copy example environment file
cp .env.example .env

# Edit with your credentials
nano .env  # or use your preferred editor
```

Add your credentials:
```bash
# REQUIRED - Get from NEO app: More → Trade API → Generate application
NEO_CONSUMER_KEY=your-consumer-key-here

NEO_MOBILE_NUMBER=+91XXXXXXXXXX
NEO_UCC=XXXXX
NEO_MPIN=123456
```

**How to get NEO_CONSUMER_KEY:**
1. Login to Kotak NEO app or website
2. Navigate to **More** tab → **Trade API** card
3. Click **Generate application**
4. Copy the token from default application
5. Paste it above as `NEO_CONSUMER_KEY`

> TOTP is a 2FA factor and is intentionally not stored in `.env` here — pass the live
> 6-digit code from your authenticator app to `totp_login(totp=...)` each time. The
> smoke test (`tests/e2e/smoke_test.py`) prompts for it by default, or auto-generates
> it if you've added a `NEO_TOTP_SECRET` to your own local `.env` for faster iteration.

## Running Tests

After installation with dev dependencies:

```bash
# Run all tests
pytest

# Run smoke tests (requires .env configuration)
python tests/e2e/smoke_test.py

# Run with coverage
pytest --cov=neo_api_client --cov-report=html
```

## IDE Setup

### VS Code

1. Install the package in editable mode
2. Select the correct Python interpreter: `Cmd+Shift+P` → "Python: Select Interpreter"
3. Choose the interpreter from your virtual environment

### PyCharm

1. Install the package in editable mode
2. Go to Settings → Project → Python Interpreter
3. Add interpreter from your virtual environment
4. Mark `neo_api_client` as Sources Root

## Next Steps

- [Quick Start Guide](../../README.md#quick-start)
- [API Documentation](../functions/README.md)
- [Run Smoke Tests](../../tests/e2e/smoke_test.py)

## Support

If you encounter issues:
- Check [GitHub Issues](https://github.com/Kotak-Neo/kotak-neo-python/issues)
- Email: support@kotakneo.com

---

[[Back to Installation]](./README.md) [[Back to Main README]](../../README.md)
