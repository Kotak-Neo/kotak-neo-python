# Installation Reference Guide

Complete reference to all installation guides available for the Kotak Neo Python SDK.

## 📚 Table of Contents

- [Quick Start](#quick-start)
- [Platform-Specific Guides](#platform-specific-guides)
- [IDE Setup Guides](#ide-setup-guides)
- [Special Installation Methods](#special-installation-methods)
- [Troubleshooting Guides](#troubleshooting-guides)

---

## Quick Start

### For Local Development (Current Method)

**📖 Guide:** [Local Installation](installation/local-install.md)

Perfect for:
- ✅ Development and testing
- ✅ Before package is published to PyPI
- ✅ Contributing to the project
- ✅ Latest features from source

**Quick Install:**
```bash
git clone https://github.com/Kotak-Neo/kotak-neo-python.git
cd kotak-neo-python
pip install -e .
```

---

## Platform-Specific Guides

### 🪟 Windows

**📖 Guide:** [Windows Installation](installation/windows.md)

Covers:
- ✅ Windows 10 and Windows 11
- ✅ Python installation via Microsoft Store or python.org
- ✅ Visual Studio Code setup
- ✅ PowerShell and Command Prompt commands
- ✅ PATH configuration
- ✅ Windows Defender considerations

**Who should use this:**
- Windows users (any version)
- Beginners setting up Python for the first time
- Users wanting IDE integration with VS Code

**Quick Reference:**
```powershell
# Install Python from Microsoft Store
# Or download from python.org

# Clone repository
git clone https://github.com/Kotak-Neo/kotak-neo-python.git
cd kotak-neo-python

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install package
pip install -e .
```

---

### 🍎 macOS

**📖 Guide:** [macOS Installation](installation/macos.md)

Covers:
- ✅ macOS Monterey, Ventura, Sonoma
- ✅ Homebrew installation
- ✅ Python installation via Homebrew or python.org
- ✅ Xcode Command Line Tools
- ✅ Terminal configuration (zsh/bash)
- ✅ VS Code setup for macOS

**Who should use this:**
- macOS users (Intel or Apple Silicon)
- Developers using Homebrew
- Users preferring native macOS tools

**Quick Reference:**
```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python@3.12

# Clone and install
git clone https://github.com/Kotak-Neo/kotak-neo-python.git
cd kotak-neo-python
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

---

### 🐧 Linux

**📖 Guide:** [Linux Installation](installation/linux.md)

Covers:
- ✅ Ubuntu/Debian
- ✅ CentOS/RHEL/Fedora
- ✅ Arch Linux
- ✅ System Python vs pyenv
- ✅ Package manager differences
- ✅ Permissions and sudo usage

**Who should use this:**
- Ubuntu, Debian users
- CentOS, RHEL, Fedora users
- Arch Linux users
- Server deployments
- Docker container setups

**Quick Reference:**

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3.10 python3-pip python3-venv

git clone https://github.com/Kotak-Neo/kotak-neo-python.git
cd kotak-neo-python
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

**CentOS/RHEL:**
```bash
sudo dnf install python3.10 python3-pip

git clone https://github.com/Kotak-Neo/kotak-neo-python.git
cd kotak-neo-python
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

---

## IDE Setup Guides

### 💻 Visual Studio Code

**📖 Guide:** [VS Code Installation](installation/vscode.md)

Covers:
- ✅ VS Code installation (all platforms)
- ✅ Python extension setup
- ✅ Workspace configuration
- ✅ Debugging setup
- ✅ Integrated terminal
- ✅ IntelliSense configuration
- ✅ Linting and formatting

**Who should use this:**
- VS Code users (all platforms)
- Developers wanting modern IDE features
- Users needing debugging tools
- Those preferring lightweight editors

**Extensions Recommended:**
- Python (ms-python.python)
- Pylance (ms-python.vscode-pylance)
- Python Debugger (ms-python.debugpy)
- Python Test Explorer
- GitLens

**Quick Setup:**
1. Install VS Code from https://code.visualstudio.com/
2. Install Python extension
3. Open kotak-neo-python folder
4. Select Python interpreter from virtual environment
5. Start coding!

---

### 🔬 PyCharm

**📖 Guide:** [PyCharm Installation](installation/pycharm.md) *(if exists)*

Covers:
- ✅ PyCharm Community/Professional
- ✅ Project setup
- ✅ Interpreter configuration
- ✅ Run configurations
- ✅ Debugging
- ✅ Testing integration

**Who should use this:**
- Professional Python developers
- Users wanting advanced refactoring tools
- Those needing database integration
- Teams using JetBrains tools

---

### 📓 Jupyter Notebook

**📖 Guide:** [Jupyter Installation](installation/jupyter.md) *(if exists)*

Covers:
- ✅ Jupyter Notebook installation
- ✅ JupyterLab setup
- ✅ Kernel configuration
- ✅ Interactive development
- ✅ Notebook examples

**Who should use this:**
- Data scientists and analysts
- Interactive development
- Prototyping and experimentation
- Documentation with code

---

### 🖥️ Command Line Only

**📖 Guide:** [CLI Installation](installation/cli.md) *(if exists)*

Covers:
- ✅ Minimal installation
- ✅ No IDE required
- ✅ Server deployments
- ✅ Automated scripts
- ✅ CI/CD pipelines

**Who should use this:**
- Server administrators
- Automated trading bots
- CI/CD pipelines
- Minimalist developers
- Headless systems

---

## Special Installation Methods

### 📦 Local Development Install

**📖 Guide:** [Local Installation](installation/local-install.md) ⭐ **RECOMMENDED**

**When to use:**
- 🔧 Package not yet on PyPI
- 🔧 Contributing to the project
- 🔧 Testing unreleased features
- 🔧 Modifying the SDK

**Installation Methods Covered:**
1. **Editable Install** (`pip install -e .`)
   - Best for development
   - Changes reflected immediately

2. **With Dev Dependencies** (`pip install -e ".[dev]"`)
   - Includes testing tools
   - Code quality tools
   - Pre-commit hooks

3. **Standard Install** (`pip install .`)
   - Production-like
   - No editable mode

4. **From Wheel** (`python -m build && pip install dist/*.whl`)
   - Clean installation
   - Distributable

---

### 🌐 From PyPI (Future)

**When available:**
```bash
pip install kotakneoapi
```

**Currently:** Package in development, not yet published to PyPI.

---

### 🔗 From GitHub

**When repository is public:**
```bash
pip install git+https://github.com/Kotak-Neo/kotak-neo-python.git
```

**Specific branch:**
```bash
pip install git+https://github.com/Kotak-Neo/kotak-neo-python.git@develop
```

**Specific tag/version:**
```bash
pip install git+https://github.com/Kotak-Neo/kotak-neo-python.git@v2.2.0
```

---

## Troubleshooting Guides

### Common Issues by Platform

#### Windows Issues

**📖 Reference:** [Windows Installation Guide - Troubleshooting Section](installation/windows.md#troubleshooting)

Common problems:
- ❌ Python not found in PATH
- ❌ pip command not recognized
- ❌ Virtual environment activation fails
- ❌ Permission errors
- ❌ SSL certificate errors

**Solutions:** See Windows guide troubleshooting section

---

#### macOS Issues

**📖 Reference:** [macOS Installation Guide - Troubleshooting Section](installation/macos.md#troubleshooting)

Common problems:
- ❌ Command Line Tools not installed
- ❌ Multiple Python versions conflict
- ❌ brew command not found
- ❌ SSL certificate errors
- ❌ M1/M2 compatibility issues

**Solutions:** See macOS guide troubleshooting section

---

#### Linux Issues

**📖 Reference:** [Linux Installation Guide - Troubleshooting Section](installation/linux.md#troubleshooting)

Common problems:
- ❌ Python version mismatch
- ❌ Missing system dependencies
- ❌ Permission denied errors
- ❌ Virtual environment issues
- ❌ Package manager conflicts

**Solutions:** See Linux guide troubleshooting section

---

## Quick Reference Matrix

| Platform | Guide | Difficulty | Time Required | Recommended For |
|----------|-------|------------|---------------|-----------------|
| **Windows** | [windows.md](installation/windows.md) | ⭐ Easy | 15-30 min | Windows users, beginners |
| **macOS** | [macos.md](installation/macos.md) | ⭐ Easy | 15-30 min | Mac users, developers |
| **Linux** | [linux.md](installation/linux.md) | ⭐⭐ Medium | 20-40 min | Linux users, servers |
| **VS Code** | [vscode.md](installation/vscode.md) | ⭐ Easy | 10-20 min | All platforms, modern IDE |
| **Local Dev** | [local-install.md](installation/local-install.md) | ⭐⭐ Medium | 10-15 min | Contributors, current use |

---

## Installation Decision Tree

### Choose Your Installation Path

```
START HERE
    │
    ├─── Are you a Windows user?
    │    └─── YES → Go to: installation/windows.md
    │
    ├─── Are you a macOS user?
    │    └─── YES → Go to: installation/macos.md
    │
    ├─── Are you a Linux user?
    │    └─── YES → Go to: installation/linux.md
    │
    ├─── Do you want to contribute/develop?
    │    └─── YES → Go to: installation/local-install.md
    │
    ├─── Using VS Code?
    │    └─── YES → Go to: installation/vscode.md
    │
    ├─── Need minimal CLI install?
    │    └─── YES → Go to: installation/cli.md
    │
    └─── Want interactive development?
         └─── YES → Go to: installation/jupyter.md
```

---

## For Different User Types

### 🆕 Beginners
**Start with:**
1. Platform-specific guide (Windows/macOS/Linux)
2. VS Code setup guide
3. Local installation guide

### 👨‍💻 Experienced Developers
**Go directly to:**
- [Local Installation Guide](installation/local-install.md)
- Quick install: `pip install -e .`

### 🏢 Enterprise Users
**Consider:**
- Linux guide for server deployments
- Virtual environment isolation
- Security best practices

### 🤝 Contributors
**Must read:**
1. [Local Installation Guide](installation/local-install.md)
2. Development dependencies section
3. Pre-commit hooks setup

---

## Installation File Structure

```
docs/
├── installation/
│   ├── README.md              # Overview of all guides
│   ├── local-install.md       # Local development install ⭐
│   ├── windows.md             # Windows-specific guide
│   ├── macos.md               # macOS-specific guide
│   ├── linux.md               # Linux-specific guide
│   ├── vscode.md              # VS Code setup
│   ├── pycharm.md             # PyCharm setup (if exists)
│   ├── jupyter.md             # Jupyter setup (if exists)
│   └── cli.md                 # CLI-only setup (if exists)
```

---

## External Resources

### Official Documentation
- 🔗 [Main README](../README.md)
- 🔗 [API Functions Documentation](functions/README.md)

### Python Resources
- 🔗 [Python Downloads](https://www.python.org/downloads/)
- 🔗 [pip Documentation](https://pip.pypa.io/)
- 🔗 [Virtual Environments Guide](https://docs.python.org/3/library/venv.html)
- 🔗 [Python Packaging Guide](https://packaging.python.org/)

### IDE Resources
- 🔗 [VS Code](https://code.visualstudio.com/)
- 🔗 [VS Code Python Extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python)
- 🔗 [PyCharm](https://www.jetbrains.com/pycharm/)
- 🔗 [Jupyter](https://jupyter.org/)

### Platform Resources
- 🔗 [Homebrew (macOS)](https://brew.sh/)
- 🔗 [Windows Package Manager](https://github.com/microsoft/winget-cli)
- 🔗 [Ubuntu Packages](https://packages.ubuntu.com/)

---

## Support & Help

### Getting Help

**Installation Issues:**
1. Check the relevant platform guide
2. Review troubleshooting section
3. Search [GitHub Issues](https://github.com/Kotak-Neo/kotak-neo-python/issues)
4. Create new issue if needed

**Contact:**
- 📧 Email: support@kotakneo.com
- 🐛 GitHub Issues: https://github.com/Kotak-Neo/kotak-neo-python/issues
- 📖 Documentation: https://github.com/Kotak-Neo/kotak-neo-python/tree/main/docs

---

## Summary

### Current Status (Package Not Yet on PyPI)

✅ **Recommended Method:** [Local Installation](installation/local-install.md)
```bash
git clone https://github.com/Kotak-Neo/kotak-neo-python.git
cd kotak-neo-python
pip install -e .
```

### Future (When Published to PyPI)

✅ **Simple Method:**
```bash
pip install kotakneoapi
```

### Platform-Specific Guides Available

| Platform | Guide | Status |
|----------|-------|--------|
| Windows | [windows.md](installation/windows.md) | ✅ Available |
| macOS | [macos.md](installation/macos.md) | ✅ Available |
| Linux | [linux.md](installation/linux.md) | ✅ Available |
| VS Code | [vscode.md](installation/vscode.md) | ✅ Available |
| Local Dev | [local-install.md](installation/local-install.md) | ✅ Available |

---

**Last Updated:** June 25, 2026  
**Package Version:** 2.2.0  
**Status:** In Development (Local Installation Only)

[[Back to Main README]](../README.md) | [[Installation Overview]](installation/README.md)
