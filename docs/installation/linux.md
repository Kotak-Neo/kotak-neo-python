# Installing kotakneoapi SDK on Linux

Complete guide to install and set up the Kotak Neo SDK on Linux distributions.

## Table of Contents
- [Prerequisites by Distribution](#prerequisites-by-distribution)
- [Installation Methods](#installation-methods)
- [Setting Up Your Project](#setting-up-your-project)
- [Visual Studio Code Setup](#visual-studio-code-setup)
- [Verification](#verification-steps)
- [Troubleshooting](#troubleshooting)

## Prerequisites by Distribution

### Ubuntu / Debian

```bash
# Update package list
sudo apt update

# Install Python 3.10 or higher
sudo apt install python3 python3-pip python3-venv -y

# Install development tools (optional but recommended)
sudo apt install build-essential python3-dev -y

# Verify installation
python3 --version
pip3 --version
```

### CentOS / RHEL / Fedora

```bash
# CentOS/RHEL 8+
sudo dnf install python3 python3-pip python3-virtualenv -y

# Fedora
sudo dnf install python3 python3-pip python3-virtualenv -y

# Development tools (optional)
sudo dnf groupinstall "Development Tools" -y

# Verify installation
python3 --version
pip3 --version
```

### Arch Linux / Manjaro

```bash
# Install Python and pip
sudo pacman -S python python-pip python-virtualenv

# Development tools (optional)
sudo pacman -S base-devel

# Verify installation
python --version
pip --version
```

### openSUSE

```bash
# Install Python and pip
sudo zypper install python3 python3-pip python3-virtualenv

# Development tools (optional)
sudo zypper install -t pattern devel_basis

# Verify installation
python3 --version
pip3 --version
```

## Installation Methods

### Method 1: Install from PyPI (Recommended)

**Step 1:** Create a project folder
```bash
mkdir -p ~/projects/my-trading-bot
cd ~/projects/my-trading-bot
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
# Ubuntu/Debian
sudo apt install git -y

# CentOS/RHEL/Fedora
sudo dnf install git -y

# Arch/Manjaro
sudo pacman -S git

# openSUSE
sudo zypper install git
```

**Step 2:** Clone the repository
```bash
cd ~/projects
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
mkdir -p ~/projects/my-trading-bot
cd ~/projects/my-trading-bot

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
NEO_TOTP_SECRET=XXXXXXXXXXXXXXXXXXXXXXXXXX
NEO_MPIN=XXXXXX
EOF
```

Secure the file:
```bash
chmod 600 .env
```

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

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# Linux
.directory
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
import pyotp
from neo_api_client import NeoAPI
from decouple import config

# Load credentials from .env file
client = NeoAPI(
    consumer_key=config("NEO_CONSUMER_KEY"),
    environment="prod",
)

# Generate the current 6-digit TOTP code from the base32 secret
totp_code = pyotp.TOTP(config("NEO_TOTP_SECRET")).now()

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

### Install VS Code

**Ubuntu/Debian:**
```bash
# Download and install from Microsoft repository
wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > packages.microsoft.gpg
sudo install -D -o root -g root -m 644 packages.microsoft.gpg /etc/apt/keyrings/packages.microsoft.gpg
sudo sh -c 'echo "deb [arch=amd64,arm64,armhf signed-by=/etc/apt/keyrings/packages.microsoft.gpg] https://packages.microsoft.com/repos/code stable main" > /etc/apt/sources.list.d/vscode.list'
rm -f packages.microsoft.gpg

sudo apt update
sudo apt install code -y
```

**Fedora/RHEL:**
```bash
sudo rpm --import https://packages.microsoft.com/keys/microsoft.asc
sudo sh -c 'echo -e "[code]\nname=Visual Studio Code\nbaseurl=https://packages.microsoft.com/yumrepos/vscode\nenabled=1\ngpgcheck=1\ngpgkey=https://packages.microsoft.com/keys/microsoft.asc" > /etc/yum.repos.d/vscode.repo'

sudo dnf check-update
sudo dnf install code -y
```

**Arch/Manjaro:**
```bash
# Install from AUR
yay -S visual-studio-code-bin

# Or using pamac
pamac install visual-studio-code-bin
```

**Snap (any distribution):**
```bash
sudo snap install --classic code
```

### Open Project in VS Code

```bash
# From project directory
code .
```

### Install Python Extension

```bash
code --install-extension ms-python.python
```

### Select Python Interpreter

1. Press `Ctrl+Shift+P`
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
Install Python using your distribution's package manager (see Prerequisites section).

### Issue: "pip: command not found"

**Solution:**
```bash
# Ubuntu/Debian
sudo apt install python3-pip -y

# CentOS/RHEL/Fedora
sudo dnf install python3-pip -y

# Arch/Manjaro
sudo pacman -S python-pip
```

### Issue: "No module named 'venv'"

**Solution:**
```bash
# Ubuntu/Debian
sudo apt install python3-venv -y

# CentOS/RHEL/Fedora
sudo dnf install python3-virtualenv -y
```

### Issue: SSL Certificate Error

**Solution:**
```bash
# Update CA certificates
sudo apt update && sudo apt install ca-certificates -y

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

### Issue: Build Errors (gcc, make not found)

**Solution:**
```bash
# Ubuntu/Debian
sudo apt install build-essential python3-dev -y

# CentOS/RHEL/Fedora
sudo dnf groupinstall "Development Tools" -y
sudo dnf install python3-devel -y

# Arch/Manjaro
sudo pacman -S base-devel
```

### Issue: Virtual Environment Not Activating

**Solution:**
```bash
# Check if venv exists
ls -la venv/

# If not, create it
python3 -m venv venv

# Activate
source venv/bin/activate

# Verify activation
which python
# Should show: /path/to/your/project/venv/bin/python
```

### Issue: Old Python Version

**Solution:**

**Ubuntu/Debian - Add deadsnakes PPA:**
```bash
sudo apt install software-properties-common -y
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install python3.12 python3.12-venv python3.12-dev -y
```

**Compile from source (any distribution):**
```bash
wget https://www.python.org/ftp/python/3.12.0/Python-3.12.0.tgz
tar -xf Python-3.12.0.tgz
cd Python-3.12.0
./configure --enable-optimizations
make -j $(nproc)
sudo make altinstall
```

### Issue: WSL (Windows Subsystem for Linux) Issues

**Solution:**
```bash
# Update WSL
wsl --update

# Inside WSL, follow Ubuntu/Debian instructions
sudo apt update
sudo apt install python3 python3-pip python3-venv -y
```

## Shell Configuration

### For bash

Add to `~/.bashrc`:
```bash
# Python virtual environment activation helper
alias venv-activate='source venv/bin/activate'
alias venv-create='python3 -m venv venv'

# Python aliases (optional)
alias python=python3
alias pip=pip3
```

Apply changes:
```bash
source ~/.bashrc
```

### For zsh

Add to `~/.zshrc`:
```bash
# Python virtual environment activation helper
alias venv-activate='source venv/bin/activate'
alias venv-create='python3 -m venv venv'

# Python aliases (optional)
alias python=python3
alias pip=pip3
```

Apply changes:
```bash
source ~/.zshrc
```

### For fish

Add to `~/.config/fish/config.fish`:
```fish
# Python virtual environment activation helper
alias venv-activate='source venv/bin/activate.fish'
alias venv-create='python3 -m venv venv'

# Python aliases (optional)
alias python=python3
alias pip=pip3
```

Apply changes:
```bash
source ~/.config/fish/config.fish
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
