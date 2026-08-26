# Jupyter Notebook Setup for kotakneoapi

Guide to installing and using the Kotak Neo SDK — including the SFeed WebSocket
live market-data client — inside Jupyter Notebook, JupyterLab, and the VS Code
Jupyter extension.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Registering a Kernel for Your Virtual Environment](#registering-a-kernel-for-your-virtual-environment)
- [Quick Start](#quick-start)
- [Async/Await in Jupyter](#asyncawait-in-jupyter)
- [SFeed WebSocket in a Notebook](#sfeed-websocket-in-a-notebook)
- [Verification Steps](#verification-steps)
- [Troubleshooting](#troubleshooting)
- [Additional Resources](#additional-resources)

## Prerequisites

- Python 3.10 or higher
- A virtual environment with `kotakneoapi` installed (see the
  [platform guides](README.md) if you haven't installed the SDK yet)

> **Windows users:** see the [Kernel crashes / restarts silently](#kernel-crashes--restarts-silently-no-traceback)
> troubleshooting entry below before you start — it covers the most common
> cause of a Jupyter kernel dying with no Python exception.

## Installation

Install Jupyter (or JupyterLab) and `ipykernel` into the **same virtual
environment** as the SDK — a kernel outside that venv won't see `kotakneoapi`:

```bash
# Activate your venv first (see the platform guide for your OS), then:
pip install notebook ipykernel
# or, for the newer JupyterLab interface:
pip install jupyterlab ipykernel
```

If you're contributing to the SDK itself and already installed with
`pip install -e ".[dev]"`, add the notebook-testing extras instead — this
repo ships a `[jupyter]` extra with the minimum needed to run and validate
notebooks headlessly (`ipykernel`, `nbconvert`, `nbformat`):

```bash
pip install -e ".[jupyter]"
```

## Registering a Kernel for Your Virtual Environment

Jupyter needs an explicit kernelspec pointing at your venv's Python —
otherwise it falls back to whatever Python it was itself installed with,
which won't have `kotakneoapi` installed:

```bash
python -m ipykernel install --user --name kotakneo --display-name "Kotak Neo SDK"
```

Then, when you open Jupyter/JupyterLab (or a notebook in VS Code), select
**"Kotak Neo SDK"** from the kernel picker in the top-right corner before
running any cells.

## Quick Start

```python
# Cell 1
from neo_api_client import NeoAPI

client = NeoAPI(consumer_key="your-consumer-key", environment="prod")
client.totp_login(mobile_number="+919876543210", ucc="ABC123", totp="123456")
client.totp_validate(mpin="123456")
```

```python
# Cell 2
quotes = client.quotes(
    instrument_tokens=[{"instrument_token": "1333", "exchange_segment": "nse_cm"}],
    quote_type="all",
)
print(quotes)
```

## Async/Await in Jupyter

This is the one thing that differs from running a plain `.py` script, and it
matters for the SFeed/order feed WebSocket clients specifically, since they're
`async`/`await` APIs.

Jupyter's kernel (`ipykernel`) already runs its own asyncio event loop in the
background, and — unlike a plain Python REPL — supports **top-level `await`**
directly in a cell:

```python
# Works in a notebook cell, no asyncio.run() needed:
async with client.create_websocket() as ws:
    ...
result = await ws.connect()
```

**Don't wrap this in `asyncio.run(...)`** the way the
[SFeed WebSocket guide](../guides/websocket.md)'s script examples do —
`asyncio.run()` starts its *own* event loop, and Jupyter's kernel already has
one running. Calling it from a cell raises:

```
RuntimeError: asyncio.run() cannot be called from a running event loop
```

That's a normal, catchable Python exception (shown as a traceback in the
cell's output) — it will **not** crash the kernel. If you see this error,
the fix is simply to `await` the coroutine directly instead of calling
`asyncio.run()` on it.

## SFeed WebSocket in a Notebook

Adapting the [Quick Start example](../guides/websocket.md#quick-start) from
the SFeed guide for a notebook — split across cells, using top-level `await`
instead of `asyncio.run(main())`:

```python
# Cell 1 — after logging in (see Quick Start above)
from neo_api_client.websocket.feed import WsToken, SFeedScrip

ws = client.create_websocket()
await ws.connect()
await ws.subscribe_scrips([
    WsToken("nse_cm", "Nifty 50"),
    WsToken("nse_cm", "11536"),
])
```

```python
# Cell 2 — run this cell, interrupt the kernel (Kernel → Interrupt, or the
# stop button) whenever you want to stop watching the feed
async for message in ws:
    if isinstance(message, SFeedScrip):
        print(
            f"{message.trading_symbol} ({message.instrument_token}) "
            f"LTP: {message.last_traded_price}"
        )
```

```python
# Cell 3 — when done
await ws.close()
```

Interrupting the kernel mid-`async for` (instead of adding your own
break condition) is the normal way to stop watching a live feed in a
notebook — `KeyboardInterrupt` propagates out of the `async for` loop the
same as it would out of a synchronous one.

## Verification Steps

Run these in a fresh cell using the kernel you registered above:

```python
import neo_api_client

print("SDK version:", neo_api_client.__version__)

from neo_api_client.websocket.feed.client import SFeedWebSocket

ws = SFeedWebSocket(access_token="dummy", sid="1", ucc="TESTUCC")
print("SFeedWebSocket constructed OK, is_connected:", ws.is_connected)
```

Both lines should print without error and without the kernel restarting. This
exercises the same import → construct path exercised by
[`tests/jupyter/sfeed_smoke.ipynb`](../../tests/jupyter/sfeed_smoke.ipynb) in
this repo, which is run in CI across Linux, Windows, and macOS
(`.github/workflows/jupyter-compatibility.yml`) on every supported Python
version specifically to catch platform-specific Jupyter breakage before it
reaches users.

## Troubleshooting

### Kernel crashes / restarts silently, no traceback

If the kernel dies — Jupyter shows "Kernel Restarting..." or "Kernel died" —
with **no Python exception or traceback**, this is not something the SDK's
own code can cause: `neo_api_client`'s WebSocket clients are pure
`asyncio` + the `websockets` library, with no threads, signal handlers, or
native/C-extension calls of their own. A silent, traceback-less process
death like this is the signature of a **native-level fault** (e.g. a
mismatched or corrupted compiled wheel for a dependency such as
`pydantic-core`, which is a Rust extension) — not a bug in the WebSocket
code path itself, even if it surfaces "on import" or "before connecting."

To isolate the cause:

1. **Reproduce outside Jupyter first.** Run the exact same code as a plain
   script: `python your_script.py`. If it crashes there too (same silent
   process death, no traceback), the issue is environment-level, not
   Jupyter-specific — skip to step 2. If it *doesn't* crash outside Jupyter,
   see [Jupyter-specific event-loop errors](#jupyter-specific-event-loop-errors)
   below instead.
2. **Rebuild your virtual environment from scratch.** A `pip install
   --force-reinstall` can still leave stale compiled files behind in
   `site-packages`. Prefer a brand-new venv:
   ```bash
   python -m venv fresh-venv
   # activate it, then:
   pip install --no-cache-dir kotakneoapi ipykernel
   ```
3. **Rule out the SDK's log file as a factor** by disabling it before import:
   ```bash
   # Windows (PowerShell)
   $env:NEO_LOG_FILE_ENABLED = "false"
   # Linux/macOS
   export NEO_LOG_FILE_ENABLED=false
   ```
   (The SDK writes a rotating log file under `./logs/` by default on
   import; this only matters if your notebook's working directory is on a
   locked/synced path, e.g. inside a live OneDrive folder.)
4. **Get the actual native fault**, since Jupyter hides it: run with Python's
   fault handler enabled outside Jupyter —
   ```bash
   python -X faulthandler your_script.py
   ```
   — or check the Windows Event Viewer (Application log) for a Python
   crash entry naming the module that faulted after reproducing the crash.
5. Share the faulthandler output / Event Viewer entry when
   [opening an issue](#getting-help) — it identifies the actual failing
   component far more precisely than "kernel died."

### Jupyter-specific event-loop errors

If instead of a silent crash you get a **catchable** error, it's almost
certainly one of these — both are expected behavior, not bugs:

- `RuntimeError: asyncio.run() cannot be called from a running event loop` —
  see [Async/Await in Jupyter](#asyncawait-in-jupyter) above; use `await`
  directly instead of `asyncio.run()`.
- `RuntimeError: This event loop is already running` from third-party code
  that itself calls `asyncio.run()` internally — install
  [`nest_asyncio`](https://pypi.org/project/nest_asyncio/) and call
  `nest_asyncio.apply()` once near the top of your notebook to allow nested
  loops.

### Kernel doesn't see `kotakneoapi`

```
ModuleNotFoundError: No module named 'neo_api_client'
```

You're on the wrong kernel. Check the kernel picker (top-right in
Jupyter/JupyterLab, or the kernel selector in VS Code) and confirm it says
the display name you registered in
[Registering a Kernel](#registering-a-kernel-for-your-virtual-environment) —
not "Python 3" or some other environment. Re-run the `ipykernel install`
command above if the kernel is missing from the list.

### `await` outside an `async` context (older Jupyter/IPython)

```
SyntaxError: 'await' outside function
```

Top-level `await` in a cell requires `ipykernel>=6.0` / IPython 7+. Upgrade:

```bash
pip install --upgrade ipykernel
```

## Additional Resources

- [SFeed WebSocket Guide](../guides/websocket.md) — full API reference for
  the async WebSocket client used above
- [Installation Guide (all platforms)](README.md)
- [Windows Installation](windows.md)
- [VS Code Setup](vscode.md) — the VS Code Jupyter extension uses the same
  kernel-registration mechanism described above
- [SDK Documentation](../../README.md)

## Getting Help

- **Issues:** https://github.com/Kotak-Neo/kotak-neo-python/issues
- **Email:** support@kotakneo.com
