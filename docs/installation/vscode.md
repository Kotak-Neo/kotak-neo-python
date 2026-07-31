# Visual Studio Code Setup for kotakneoapi

Complete guide to set up Visual Studio Code for Python development with the Kotak Neo SDK.

## Prerequisites

- Visual Studio Code installed
- Python 3.10+ installed
- kotakneoapi SDK installed

> See platform-specific guides: [Windows](windows.md) | [macOS](macos.md) | [Linux](linux.md)

## Quick Setup

```bash
# Install VS Code Python extension
code --install-extension ms-python.python

# Open your project
cd ~/projects/my-trading-bot
code .
```

## Essential Extensions

### 1. Python Extension (Required)

```bash
code --install-extension ms-python.python
```

**Features:**
- IntelliSense (autocompletion)
- Linting and formatting
- Debugging
- Jupyter Notebook support

### 2. Pylance (Recommended)

```bash
code --install-extension ms-python.vscode-pylance
```

**Features:**
- Fast type checking
- Better IntelliSense
- Auto-imports
- Type information

### 3. Ruff (Recommended)

```bash
code --install-extension charliermarsh.ruff
```

**Features:**
- Lint/format using this project's actual toolchain (see `pyproject.toml`) — not flake8/black/pylint
- Inline diagnostics
- Format-on-save support

### 4. Python Indent

```bash
code --install-extension KevinRose.vsc-python-indent
```

**Features:**
- Correct Python indentation
- Smart dedenting

### 5. autoDocstring

```bash
code --install-extension njpwerner.autodocstring
```

**Features:**
- Generate docstrings automatically
- Multiple formats (Google, NumPy, Sphinx)

### 6. GitLens

```bash
code --install-extension eamodio.gitlens
```

**Features:**
- Git blame annotations
- Commit history
- File history

### 7. Error Lens

```bash
code --install-extension usernamehw.errorlens
```

**Features:**
- Inline error messages
- Warnings highlighted

## Project Configuration

### 1. Workspace Settings

Create `.vscode/settings.json`:

This project lints and formats with [ruff](https://docs.astral.sh/ruff/) (see
`pyproject.toml`), not flake8/black/pylint — install the `charliermarsh.ruff`
extension (see [Essential Extensions](#essential-extensions) below) alongside
the settings here for inline linting and format-on-save.

**For Windows:**
```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}\\venv\\Scripts\\python.exe",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    },
    "[python]": {
        "editor.tabSize": 4,
        "editor.insertSpaces": true,
        "editor.rulers": [100],
        "editor.defaultFormatter": "charliermarsh.ruff"
    },
    "python.testing.pytestEnabled": true,
    "python.testing.unittestEnabled": false,
    "python.testing.pytestArgs": [
        "tests"
    ],
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        "**/.pytest_cache": true,
        "**/.coverage": true,
        "**/htmlcov": true
    },
    "files.watcherExclude": {
        "**/__pycache__/**": true,
        "**/venv/**": true
    }
}
```

**For macOS/Linux:**
```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    },
    "[python]": {
        "editor.tabSize": 4,
        "editor.insertSpaces": true,
        "editor.rulers": [100],
        "editor.defaultFormatter": "charliermarsh.ruff"
    },
    "python.testing.pytestEnabled": true,
    "python.testing.unittestEnabled": false,
    "python.testing.pytestArgs": [
        "tests"
    ],
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        "**/.pytest_cache": true,
        "**/.coverage": true,
        "**/htmlcov": true,
        "**/.DS_Store": true
    },
    "files.watcherExclude": {
        "**/__pycache__/**": true,
        "**/venv/**": true
    }
}
```

### 2. Launch Configuration

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
            "envFile": "${workspaceFolder}/.env",
            "justMyCode": true
        },
        {
            "name": "Python: Trading Bot",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/main.py",
            "console": "integratedTerminal",
            "envFile": "${workspaceFolder}/.env"
        },
        {
            "name": "Python: Debug Tests",
            "type": "python",
            "request": "launch",
            "module": "pytest",
            "args": [
                "-v",
                "--tb=short"
            ],
            "console": "integratedTerminal"
        }
    ]
}
```

### 3. Tasks Configuration

Create `.vscode/tasks.json`:

```json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Run Tests",
            "type": "shell",
            "command": "${config:python.defaultInterpreterPath}",
            "args": [
                "-m",
                "pytest",
                "-v"
            ],
            "group": {
                "kind": "test",
                "isDefault": true
            },
            "presentation": {
                "reveal": "always",
                "panel": "new"
            }
        },
        {
            "label": "Run Coverage",
            "type": "shell",
            "command": "${config:python.defaultInterpreterPath}",
            "args": [
                "-m",
                "pytest",
                "--cov=.",
                "--cov-report=html"
            ],
            "group": "test",
            "presentation": {
                "reveal": "always",
                "panel": "new"
            }
        },
        {
            "label": "Format Code",
            "type": "shell",
            "command": "${config:python.defaultInterpreterPath}",
            "args": [
                "-m",
                "ruff",
                "format",
                "."
            ],
            "group": "build",
            "presentation": {
                "reveal": "always",
                "panel": "new"
            }
        },
        {
            "label": "Lint Code",
            "type": "shell",
            "command": "${config:python.defaultInterpreterPath}",
            "args": [
                "-m",
                "ruff",
                "check",
                "."
            ],
            "group": "build",
            "presentation": {
                "reveal": "always",
                "panel": "new"
            }
        }
    ]
}
```

## Python Interpreter Setup

### Select Interpreter

1. Press `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (macOS)
2. Type: "Python: Select Interpreter"
3. Choose your virtual environment:
   - Windows: `.\venv\Scripts\python.exe`
   - macOS/Linux: `./venv/bin/python`

### Manual Interpreter Path

If VS Code doesn't find your interpreter:

1. Press `Ctrl+Shift+P` / `Cmd+Shift+P`
2. Type: "Python: Select Interpreter"
3. Click "Enter interpreter path..."
4. Browse to your venv Python executable

## Keyboard Shortcuts

### Essential Shortcuts

| Action | Windows/Linux | macOS |
|--------|---------------|-------|
| Command Palette | `Ctrl+Shift+P` | `Cmd+Shift+P` |
| Quick Open | `Ctrl+P` | `Cmd+P` |
| Run Python File | `Ctrl+F5` | `Cmd+F5` |
| Debug Python File | `F5` | `F5` |
| Run Selection | `Shift+Enter` | `Shift+Enter` |
| Format Document | `Shift+Alt+F` | `Shift+Option+F` |
| Go to Definition | `F12` | `F12` |
| Peek Definition | `Alt+F12` | `Option+F12` |
| Find All References | `Shift+F12` | `Shift+F12` |
| Rename Symbol | `F2` | `F2` |
| Toggle Terminal | `` Ctrl+` `` | `` Cmd+` `` |
| Toggle Sidebar | `Ctrl+B` | `Cmd+B` |

### Custom Keybindings

Create `.vscode/keybindings.json`:

```json
[
    {
        "key": "ctrl+shift+t",
        "command": "python.execInTerminal",
        "when": "editorTextFocus && editorLangId == 'python'"
    },
    {
        "key": "ctrl+shift+r",
        "command": "workbench.action.tasks.runTask",
        "args": "Run Tests"
    }
]
```

## Code Snippets

### Create Custom Snippets

1. Press `Ctrl+Shift+P` / `Cmd+Shift+P`
2. Type: "Preferences: Configure User Snippets"
3. Select "python.json"

Add Neo API snippets:

```json
{
    "Neo API Client": {
        "prefix": "neo-client",
        "body": [
            "from neo_api_client import NeoAPI",
            "from decouple import config",
            "",
            "client = NeoAPI(",
            "    consumer_key=config(\"NEO_CONSUMER_KEY\"),",
            "    environment=\"prod\"",
            ")",
            "$0"
        ],
        "description": "Create Neo API client"
    },
    "Neo Login": {
        "prefix": "neo-login",
        "body": [
            "import pyotp",
            "",
            "# Step 1: Login with TOTP",
            "totp_code = pyotp.TOTP(config(\"NEO_TOTP_SECRET\")).now()",
            "client.totp_login(",
            "    mobile_number=config(\"NEO_MOBILE_NUMBER\"),",
            "    ucc=config(\"NEO_UCC\"),",
            "    totp=totp_code,",
            ")",
            "",
            "# Step 2: Validate with MPIN to complete authentication",
            "client.totp_validate(mpin=config(\"NEO_MPIN\"))",
            "$0"
        ],
        "description": "Neo API login flow"
    },
    "Neo Place Order": {
        "prefix": "neo-order",
        "body": [
            "order = client.place_order(",
            "    exchange_segment=\"${1|nse_cm,bse_cm,nse_fo|}\"," ,
            "    product=\"${2|CNC,MIS,NRML|}\",",
            "    price=\"${3:100.50}\",",
            "    order_type=\"${4|L,MKT,SL,SL-M|}\",",
            "    quantity=\"${5:1}\",",
            "    validity=\"${6|DAY,IOC|}\",",
            "    trading_symbol=\"${7:RELIANCE-EQ}\",",
            "    transaction_type=\"${8|B,S|}\"",
            ")",
            "print(order)",
            "$0"
        ],
        "description": "Place order with Neo API"
    }
}
```

## Debugging

### Breakpoints

- Click in the gutter (left of line numbers) to set breakpoints
- Or press `F9` while cursor is on a line

### Debug Console

- Press `Ctrl+Shift+Y` / `Cmd+Shift+Y`
- Evaluate expressions while debugging
- Example: `client.configuration.base_url`

### Debug Tips

1. **Conditional Breakpoints:**
   - Right-click breakpoint
   - Select "Edit Breakpoint"
   - Add condition: `order_id == "123"`

2. **Logpoints:**
   - Right-click gutter
   - Select "Add Logpoint"
   - Add message: `Order placed: {order_id}`

3. **Watch Variables:**
   - Click "+" in Watch panel
   - Add variable: `client.configuration`

## Testing in VS Code

### Run Tests

1. Open Test Explorer (beaker icon in sidebar)
2. Click "Configure Python Tests"
3. Select "pytest"
4. Select "tests" folder

### Run Specific Test

- Click play button next to test
- Or right-click test → "Run Test"

### Debug Test

- Right-click test → "Debug Test"
- Breakpoints work in tests

## IntelliSense and Autocomplete

### Trigger IntelliSense

- Type and pause (auto-trigger)
- Or press `Ctrl+Space`

### Quick Documentation

- Hover over any function/class
- Or press `Ctrl+K Ctrl+I` / `Cmd+K Cmd+I`

### Parameter Hints

- Press `Ctrl+Shift+Space` / `Cmd+Shift+Space`
- Shows function parameters

## Linting and Formatting

### Install Linters

`ruff` and `mypy` ship with the SDK's dev dependencies (`pip install -e ".[dev]"`);
install standalone only if you're linting a bare venv:
```bash
pip install ruff mypy
```

### Format on Save

Already configured in `settings.json`:
```json
"editor.formatOnSave": true
```

### Manual Formatting

- Press `Shift+Alt+F` / `Shift+Option+F`
- Or right-click → "Format Document"

### Organize Imports

- Right-click → "Organize Imports"
- Or save (auto-organized if configured)

## Terminal Integration

### Integrated Terminal

- Press `` Ctrl+` `` / `` Cmd+` ``
- Automatically activates virtual environment

### Multiple Terminals

- Click "+" in terminal panel
- Each can have different shell

### Terminal Shortcuts

```json
// Add to keybindings.json
{
    "key": "ctrl+shift+t",
    "command": "workbench.action.terminal.new"
}
```

## Git Integration

### Source Control Panel

- Press `Ctrl+Shift+G` / `Cmd+Shift+G`
- View changes, stage, commit

### Commit

1. Stage changes (click "+")
2. Enter commit message
3. Press `Ctrl+Enter` / `Cmd+Enter`

### View Git History

- Install GitLens extension
- Click file → "Open File History"

## Troubleshooting

### Issue: IntelliSense Not Working

**Solution:**
1. Select correct Python interpreter
2. Reload window: `Ctrl+Shift+P` → "Developer: Reload Window"
3. Restart Python Language Server: `Ctrl+Shift+P` → "Python: Restart Language Server"

### Issue: Linter Not Running

**Solution:**
```bash
# Ensure ruff is installed in venv
pip install ruff
```
Then confirm the `charliermarsh.ruff` extension is installed and enabled — it
picks up lint/format config from `pyproject.toml` automatically, no
`settings.json` linting flags required.

### Issue: Debugger Not Stopping at Breakpoints

**Solution:**
1. Check `"justMyCode": true` in launch.json
2. Ensure file is saved
3. Rebuild: `Ctrl+Shift+P` → "Python: Build Workspace Symbols"

### Issue: Import Errors but Code Runs

**Solution:**
1. Verify interpreter: `Ctrl+Shift+P` → "Python: Select Interpreter"
2. Check extraPaths in settings:
```json
{
    "python.analysis.extraPaths": [
        "./src"
    ]
}
```

## Recommended Global Settings

Press `Ctrl+,` / `Cmd+,` to open settings, add:

```json
{
    "files.autoSave": "afterDelay",
    "files.autoSaveDelay": 1000,
    "editor.minimap.enabled": true,
    "editor.rulers": [100],
    "editor.renderWhitespace": "boundary",
    "editor.bracketPairColorization.enabled": true,
    "workbench.colorTheme": "Default Dark+",
    "terminal.integrated.fontSize": 13,
    "editor.fontSize": 14,
    "editor.lineHeight": 20
}
```

## Performance Tips

1. **Exclude Large Folders:**
```json
{
    "files.watcherExclude": {
        "**/venv/**": true,
        "**/node_modules/**": true,
        "**/.git/**": true
    }
}
```

2. **Disable Unused Extensions:**
   - Click Extensions icon
   - Right-click unused extension
   - Select "Disable (Workspace)"

3. **Reduce IntelliSense Delay:**
```json
{
    "editor.quickSuggestionsDelay": 0
}
```

## Next Steps

1. ✅ VS Code configured
2. 📝 Create your trading bot code
3. 🐛 Use debugging features
4. 🧪 Run tests in Test Explorer
5. 🚀 Deploy your bot!

## Additional Resources

- [VS Code Python Tutorial](https://code.visualstudio.com/docs/python/python-tutorial)
- [VS Code Debugging](https://code.visualstudio.com/docs/editor/debugging)
- [Python in VS Code](https://code.visualstudio.com/docs/languages/python)
- [SDK Documentation](../../README.md)

## Getting Help

- **Issues:** https://github.com/Kotak-Neo/kotak-neo-python/issues
- **Email:** support@kotakneo.com
