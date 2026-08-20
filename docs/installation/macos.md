# Installing kotakneoapi SDK on macOS

Complete guide to install and set up the Kotak Neo SDK on macOS (Intel and Apple Silicon).

## Table of Contents
- [Prerequisites](#prerequisites)
- [Installation Methods](#installation-methods)
- [Setting Up Your Project](#setting-up-your-project)
- [Visual Studio Code Setup](#visual-studio-code-setup)
- [Verification](#verification-steps)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### 1. Install Homebrew (Recommended)

Homebrew is the package manager for macOS. If you don't have it:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

**For Apple Silicon (M1/M2/M3)**, add Homebrew to PATH:
```bash
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

Verify:
```bash
brew --version
# Should output: Homebrew 4.x.x
```

### 2. Install Python

**Option A: Using Homebrew (Recommended)**
```bash
# Install Python 3.12 (or latest version)
brew install python@3.12

# Verify installation
python3 --version
# Should output: Python 3.12.x or higher

pip3 --version
# Should output: pip 23.x.x or higher
```

**Option B: From python.org**
1. Go to https://www.python.org/downloads/macos/
2. Download the latest Python 3.10+ installer
3. Run the installer
4. Verify: `python3 --version`

### 3. Install Visual Studio Code (Optional but Recommended)

**Option A: Using Homebrew**
```bash
brew install --cask visual-studio-code
```

**Option B: Manual Download**
1. Download from https://code.visualstudio.com/
2. Drag to Applications folder
3. Open VS Code and install shell command:
   - Press `Cmd+Shift+P`
   - Type "Shell Command: Install 'code' command in PATH"
   - Press Enter

### 4. Install VS Code Python Extension

```bash
code --install-extension ms-python.python
```

Or manually:
1. Open VS Code
2. Press `Cmd+Shift+X`
3. Search for "Python"
4. Install "Python" extension by Microsoft

## Installation Methods

### Method 1: Install from PyPI (Recommended)

**Step 1:** Create a project folder
```bash
mkdir -p ~/Projects/my-trading-bot
cd ~/Projects/my-trading-bot
```

**Step 2:** Create virtual environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate
```

**Step 3:** Install the SDK
```bash
pip install kotakneoapi
```

**Step 4:** Verify installation
```bash
pip show kotakneoapi
python -c "from neo_api_client import NeoAPI; print('✓ Installation successful')"
```

### Method 2: Install from Source (Development)

**Step 1:** Install Git (if not already installed)
```bash
# Check if git is installed
git --version

# If not, install via Homebrew
brew install git
```

**Step 2:** Clone the repository
```bash
cd ~/Projects
git clone https://github.com/Kotak-Neo/kotak-neo-python.git
cd kotak-neo-python
```

**Step 3:** Create virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

**Step 4:** Install in editable mode with dev dependencies
```bash
pip install -e ".[dev]"
```

### Method 3: Install from GitHub (Direct)

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install directly from GitHub
pip install git+https://github.com/Kotak-Neo/kotak-neo-python.git
```

## Setting Up Your Project

### Step 1: Create Project Structure

```bash
# Create project directory
mkdir -p ~/Projects/my-trading-bot
cd ~/Projects/my-trading-bot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install SDK
pip install kotakneoapi

# Create project files
touch main.py .env .gitignore
```

### Step 2: Set Up Environment Variables

Create `.env` file:
```bash
cat > .env << 'EOF'
NEO_CONSUMER_KEY=your-consumer-key-token-here
NEO_MOBILE_NUMBER=+91XXXXXXXXXX
NEO_UCC=XXXXX
NEO_MPIN=XXXXXX
EOF
```

> TOTP is a 2FA factor and is intentionally not stored in `.env` here — the sample
> script below prompts for the live 6-digit code from your authenticator app instead.

Create `.gitignore` file:
```bash
cat > .gitignore << 'EOF'
# Virtual environment
venv/
.env

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.so
*.egg
*.egg-info/
dist/
build/

# macOS
.DS_Store
.AppleDouble
.LSOverride

# VS Code
.vscode/

# PyCharm
.idea/
EOF
```

### Step 3: Install python-decouple for .env Support

`python-decouple` ships as a core dependency of `kotakneoapi`, so a separate
install isn't required if the SDK is already installed. Shown here for
clarity in case you're using a bare venv:
```bash
pip install python-decouple
```

### Step 4: Create Sample Script

Create `main.py`:
```python
from neo_api_client import NeoAPI
from decouple import config

# Load credentials from .env file
client = NeoAPI(
    consumer_key=config("NEO_CONSUMER_KEY"),
    environment="prod",
)

# Enter the live 6-digit code from your authenticator app.
totp_code = input("Enter TOTP code: ").strip()

# Step 1: Login with TOTP
client.totp_login(
    mobile_number=config("NEO_MOBILE_NUMBER"),
    ucc=config("NEO_UCC"),
    totp=totp_code,
)

# Step 2: Validate with MPIN to complete authentication
client.totp_validate(mpin=config("NEO_MPIN"))

# Get quotes
quotes = client.quotes(
    instrument_tokens=[{"instrument_token": "1333", "exchange_segment": "nse_cm"}], quote_type="all"
)

print(quotes)
```

### Step 5: Run Your Script

```bash
python main.py
```

## Visual Studio Code Setup

### Open Project in VS Code

```bash
# From project directory
code .
```

### Select Python Interpreter

1. Press `Cmd+Shift+P`
2. Type "Python: Select Interpreter"
3. Choose: `./venv/bin/python`

### Recommended Extensions

```bash
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
code --install-extension charliermarsh.ruff
code --install-extension KevinRose.vsc-python-indent
code --install-extension njpwerner.autodocstring
code --install-extension eamodio.gitlens
code --install-extension usernamehw.errorlens
```

Or install manually:
1. **Python** (Microsoft) - Core Python support
2. **Pylance** - Enhanced IntelliSense
3. **Ruff** - Linting/formatting (this project's toolchain)
4. **Python Indent** - Correct indentation
5. **autoDocstring** - Generate docstrings
6. **GitLens** - Git integration
7. **Error Lens** - Inline errors

### VS Code Settings

Create `.vscode/settings.json`:
```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
    "editor.formatOnSave": true,
    "[python]": {
        "editor.defaultFormatter": "charliermarsh.ruff"
    },
    "python.testing.pytestEnabled": true,
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        "**/.DS_Store": true
    }
}
```

This project lints and formats with [ruff](https://docs.astral.sh/ruff/) (see
`pyproject.toml`), not flake8/black/pylint — install the
`charliermarsh.ruff` VS Code extension alongside the Python extension for
inline linting and format-on-save.

### Create Launch Configuration

Create `.vscode/launch.json`:
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Current File",
            "type": "python",
            "request": "launch",
            "program": "${file}",
            "console": "integratedTerminal",
            "envFile": "${workspaceFolder}/.env"
        }
    ]
}
```

## Verification Steps

### 1. Verify Installation

```bash
# Check installed packages
pip list | grep kotakneoapi

# Should show the installed version, e.g.: kotakneoapi    3.0.1
```

### 2. Test Import

```bash
python -c "from neo_api_client import NeoAPI; print('✓ SDK imported successfully')"
```

### 3. Check Version

```bash
python -c "from neo_api_client import __version__; print(f'Version: {__version__}')"
```

### 4. Run Test Script

Create `test_install.py`:
```python
from neo_api_client import NeoAPI, __version__

print(f"✓ kotakneoapi version: {__version__}")

client = NeoAPI(consumer_key="test_key", environment="prod")

print("✓ NeoAPI client created successfully")
print("✓ Installation verified!")
```

Run:
```bash
python test_install.py
```

## Troubleshooting

### Issue: "python3: command not found"

**Solution:**
```bash
# Install Python via Homebrew
brew install python@3.12

# Add to PATH (if needed)
echo 'export PATH="/usr/local/opt/python@3.12/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Issue: "pip: command not found"

**Solution:**
```bash
# Upgrade pip
python3 -m ensurepip --upgrade
python3 -m pip install --upgrade pip
```

### Issue: SSL Certificate Error

**Solution:**
```bash
# Update certificates
pip install --upgrade certifi

# Or install with trusted hosts
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org kotakneoapi
```

### Issue: Permission Denied

**Solution:**
Always use virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate
pip install kotakneoapi
```

If you must install globally (not recommended):
```bash
pip install --user kotakneoapi
```

### Issue: Virtual Environment Not Activating

**Solution:**
Check your shell:
```bash
# For zsh (default on macOS Catalina+)
source venv/bin/activate

# For bash
source venv/bin/activate

# Verify activation
which python
# Should show: /path/to/your/project/venv/bin/python
```

### Issue: Command Line Tools Not Installed

**Solution:**
```bash
xcode-select --install
```

### Issue: Homebrew Installation Fails

**Solution:**
```bash
# Remove incomplete installation
rm -rf /opt/homebrew

# Reinstall
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Issue: VS Code Not Finding Python

**Solution:**
1. Press `Cmd+Shift+P`
2. Type "Python: Select Interpreter"
3. Click "Enter interpreter path"
4. Browse to: `~/Projects/my-trading-bot/venv/bin/python`

### Issue: Apple Silicon (M1/M2/M3) Compatibility

**Solution:**
```bash
# Install under Rosetta if needed
arch -x86_64 pip install kotakneoapi

# Or use native ARM build (recommended)
pip install kotakneoapi
```

## Updating the SDK

```bash
# Activate virtual environment
source venv/bin/activate

# Upgrade to latest version
pip install --upgrade kotakneoapi

# Verify new version
pip show kotakneoapi
```

## Uninstalling the SDK

```bash
# Activate virtual environment
source venv/bin/activate

# Uninstall
pip uninstall kotakneoapi

# Confirm with 'y'
```

## Shell Configuration

### For zsh (default on macOS Catalina+)

Edit `~/.zshrc`:
```bash
# Add aliases for convenience
alias python=python3
alias pip=pip3

# Python virtual environment activation helper
alias venv-activate='source venv/bin/activate'
```

Apply changes:
```bash
source ~/.zshrc
```

### For bash

Edit `~/.bash_profile` or `~/.bashrc`:
```bash
# Add aliases for convenience
alias python=python3
alias pip=pip3

# Python virtual environment activation helper
alias venv-activate='source venv/bin/activate'
```

Apply changes:
```bash
source ~/.bash_profile
```

## Quick Reference Commands

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Deactivate
deactivate

# Install package
pip install kotakneoapi

# Install with dev dependencies
pip install -e ".[dev]"

# List installed packages
pip list

# Show package info
pip show kotakneoapi

# Upgrade package
pip install --upgrade kotakneoapi

# Uninstall package
pip uninstall kotakneoapi

# Freeze dependencies
pip freeze > requirements.txt

# Install from requirements
pip install -r requirements.txt
```

## Next Steps

1. ✅ SDK installed successfully
2. 📝 Set up your `.env` file with credentials
3. 🎯 Try the sample script in `main.py`
4. 📚 Read the [API Documentation](../README.md)
5. 🚀 Build your trading bot!

## Additional Resources

- [SDK Documentation](../../README.md)
- [VS Code Setup Guide](vscode.md)
- [PyCharm Setup Guide](pycharm.md)
- [Kotak Neo API Docs](https://developers.kotaksecurities.com/)

## Getting Help

- **Issues:** https://github.com/Kotak-Neo/kotak-neo-python/issues
- **Email:** support@kotakneo.com
