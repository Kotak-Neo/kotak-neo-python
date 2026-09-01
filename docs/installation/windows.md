# Installing kotakneoapi SDK on Windows

Complete guide to install and set up the Kotak Neo SDK on Windows 10/11.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Installation Methods](#installation-methods)
- [Setting Up Your Project](#setting-up-your-project)
- [Visual Studio Code Setup](#visual-studio-code-setup)
- [Verification](#verification-steps)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### 1. Install Python

**Download and Install Python:**
1. Go to https://www.python.org/downloads/windows/
2. Download Python 3.10 or higher (recommended: latest stable version)
3. Run the installer
4. ✅ **IMPORTANT:** Check "Add Python to PATH" during installation
5. Click "Install Now"

**Verify Installation:**
```powershell
# Open PowerShell or Command Prompt and run:
python --version
# Should output: Python 3.10.x or higher

pip --version
# Should output: pip 23.x.x or higher
```

### 2. Install Visual Studio Code (Optional but Recommended)

1. Download from https://code.visualstudio.com/
2. Run the installer
3. During installation, check:
   - ✅ "Add to PATH"
   - ✅ "Add 'Open with Code' action to Windows Explorer file context menu"
   - ✅ "Add 'Open with Code' action to Windows Explorer directory context menu"

### 3. Install VS Code Python Extension

1. Open Visual Studio Code
2. Click Extensions icon (or press `Ctrl+Shift+X`)
3. Search for "Python"
4. Install "Python" extension by Microsoft
5. Restart VS Code

## Installation Methods

### Method 1: Install from PyPI (Recommended)

**Step 1:** Create a project folder
```powershell
# Open PowerShell
mkdir C:\Projects\my-trading-bot
cd C:\Projects\my-trading-bot
```

**Step 2:** Create virtual environment
```powershell
# Create virtual environment
python -m venv venv

# Activate it
.\venv\Scripts\Activate.ps1
```

> **Note:** If you get execution policy error, run:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

**Step 3:** Install the SDK
```powershell
pip install kotakneoapi
```

**Step 4:** Verify installation
```powershell
pip show kotakneoapi
python -c "from neo_api_client import NeoAPI; print('✓ Installation successful')"
```

### Method 2: Install from Source (Development)

**Step 1:** Install Git for Windows
1. Download from https://git-scm.com/download/win
2. Run installer (use default settings)

**Step 2:** Clone the repository
```powershell
# Open PowerShell
cd C:\Projects
git clone https://github.com/Kotak-Neo/kotak-neo-python.git
cd kotak-neo-python
```

**Step 3:** Create virtual environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Step 4:** Install in editable mode with dev dependencies
```powershell
pip install -e ".[dev]"
```

### Method 3: Install from GitHub (Direct)

```powershell
# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install directly from GitHub
pip install git+https://github.com/Kotak-Neo/kotak-neo-python.git
```

## Setting Up Your Project

### Step 1: Create Project Structure

```powershell
# Create project directory
mkdir C:\Projects\my-trading-bot
cd C:\Projects\my-trading-bot

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install SDK
pip install kotakneoapi

# Create project files
New-Item -ItemType File -Name "main.py"
New-Item -ItemType File -Name ".env"
New-Item -ItemType File -Name ".gitignore"
```

### Step 2: Set Up Environment Variables

Create `.env` file:
```env
NEO_CONSUMER_KEY=your-consumer-key-token-here
NEO_MOBILE_NUMBER=+91XXXXXXXXXX
NEO_UCC=XXXXX
NEO_MPIN=XXXXXX
```

> TOTP is a 2FA factor and is intentionally not stored in `.env` here — the sample
> script below prompts for the live 6-digit code from your authenticator app instead.

Create `.gitignore` file:
```
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

# VS Code
.vscode/
```

### Step 3: Install python-decouple for .env Support

`python-decouple` ships as a core dependency of `kotakneoapi`, so a separate
install isn't required if the SDK is already installed. Shown here for
clarity in case you're using a bare venv:
```powershell
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

**In Terminal:**
```powershell
python main.py
```

**In VS Code:**
1. Open `main.py`
2. Press `Ctrl+F5` to run without debugging
3. Or press `F5` to run with debugging

## Visual Studio Code Setup

### Open Project in VS Code

```powershell
# From project directory
code .
```

### Select Python Interpreter

1. Press `Ctrl+Shift+P`
2. Type "Python: Select Interpreter"
3. Choose: `.\venv\Scripts\python.exe`

### Recommended Extensions

Install these extensions for better Python development:

```powershell
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
    "python.defaultInterpreterPath": "${workspaceFolder}\\venv\\Scripts\\python.exe",
    "editor.formatOnSave": true,
    "[python]": {
        "editor.defaultFormatter": "charliermarsh.ruff"
    },
    "python.testing.pytestEnabled": true,
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true
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

```powershell
# Check installed packages
pip list | Select-String "kotakneoapi"

# Should show the installed version, e.g.: kotakneoapi    3.0.3
```

### 2. Test Import

```powershell
python -c "from neo_api_client import NeoAPI; print('✓ SDK imported successfully')"
```

### 3. Check Version

```powershell
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
```powershell
python test_install.py
```

## Troubleshooting

### Issue: "python is not recognized"

**Solution:**
1. Add Python to PATH manually:
   - Open "Environment Variables"
   - Add to PATH: `C:\Users\YourUsername\AppData\Local\Programs\Python\Python310\`
   - Add to PATH: `C:\Users\YourUsername\AppData\Local\Programs\Python\Python310\Scripts\`
2. Restart PowerShell/Command Prompt

### Issue: "Activate.ps1 cannot be loaded"

**Solution:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Issue: "pip install fails with SSL error"

**Solution:**
```powershell
python -m pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org kotakneoapi
```

### Issue: VS Code not detecting virtual environment

**Solution:**
1. Press `Ctrl+Shift+P`
2. Type "Python: Select Interpreter"
3. Click "Enter interpreter path"
4. Browse to: `C:\Projects\my-trading-bot\venv\Scripts\python.exe`

### Issue: Import errors in VS Code

**Solution:**
1. Ensure virtual environment is activated (you should see `(venv)` in terminal)
2. Restart VS Code
3. Reload window: `Ctrl+Shift+P` → "Developer: Reload Window"

### Issue: pip is outdated

**Solution:**
```powershell
python -m pip install --upgrade pip
```

### Issue: ModuleNotFoundError after installation

**Solution:**
```powershell
# Verify you're in the correct virtual environment
.\venv\Scripts\Activate.ps1

# Reinstall
pip uninstall kotakneoapi
pip install kotakneoapi
```

## Updating the SDK

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Upgrade to latest version
pip install --upgrade kotakneoapi

# Verify new version
pip show kotakneoapi
```

## Uninstalling the SDK

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Uninstall
pip uninstall kotakneoapi

# Confirm with 'y'
```

## PowerShell vs Command Prompt

### Activate Virtual Environment

**PowerShell:**
```powershell
.\venv\Scripts\Activate.ps1
```

**Command Prompt (cmd):**
```cmd
.\venv\Scripts\activate.bat
```

**Git Bash:**
```bash
source venv/Scripts/activate
```

### Deactivate Virtual Environment

All shells:
```
deactivate
```

## Quick Reference Commands

```powershell
# Create virtual environment
python -m venv venv

# Activate (PowerShell)
.\venv\Scripts\Activate.ps1

# Activate (CMD)
.\venv\Scripts\activate.bat

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
