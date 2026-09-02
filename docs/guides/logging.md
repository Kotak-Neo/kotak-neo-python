# Logging Guide

The SDK uses [`structlog`](https://www.structlog.org/) for structured logging across
both REST and WebSocket (`SFeedWebSocket`/`OrderFeedWebSocket`) clients. It's quiet by
default and configurable via `setup_logging()` or environment variables.

## Quick Start

```python
from neo_api_client.logger import setup_logging

# Console at INFO, file at its own default (WARNING+, rotates daily).
setup_logging(level="INFO")

# Console fully off, file at INFO+ instead -- useful when you don't want
# log output cluttering the console but still want a detailed record.
setup_logging(level="NOLOG", file_level="INFO")
```

`level` (console) and `file_level` (file) are independent. Both accept `"NOLOG"` to
disable that output entirely. Calling `setup_logging(...)` fully replaces the previous
configuration rather than adding to it, so it's safe to call again at runtime to
reconfigure.

## Rotating log file

On by default, and covers REST *and* WebSocket. Written to
`logs/neo-api-client.log` (relative to your working directory), rotated daily with 7
days retained, independent of the console level.

| Env var | Purpose | Default |
|---|---|---|
| `NEO_LOG_LEVEL` | Console log level | `WARNING` |
| `NEO_LOG_JSON` | Console output as JSON (`false` for colored text) | `true` |
| `NEO_LOG_FILE_ENABLED` | Enable/disable the rotating file | `true` |
| `NEO_LOG_FILE_PATH` | File path | `logs/neo-api-client.log` |
| `NEO_LOG_FILE_LEVEL` | File log level | `WARNING` |
| `NEO_LOG_FILE_BACKUP_COUNT` | Days of rotated files to keep | `7` |

## Log levels used by the SDK

Set `level`/`file_level` to the lowest one you want to see — each level also includes
everything above it.

| Level | What's logged |
|-------|----------------|
| `INFO` | Trade REST request/response tracing — `api_request_start` (method, URL, query params, body) and `api_request_success` (status, duration, response body) — a `function_call`/`function_result` snapshot (function name, params, result) for `totp_login()`/`totp_validate()`, rate-limiter/circuit-breaker lifecycle events, a successful WebSocket connect/authenticate/reconnect/subscribe/unsubscribe (SFeed's `sfeed_subscribed`/`sfeed_unsubscribed` include the actual `instrument_tokens` list, not just a count), every SFeed message (`sfeed_message_received` per delivered tick, with `instrument_token`/`exchange_segment`/`trading_symbol`), and every order-feed packet (`orderfeed_order_update` with `order_id`+`order_status`, `orderfeed_position_update`, or `orderfeed_message_received` for anything else). |
| `WARNING` | Recoverable issues: a WebSocket connect/reconnect attempt failing (before the next retry), a disconnect, a retried request, or a circuit breaker reopening/rejecting a call. |
| `ERROR` | Failures: REST 4xx/5xx responses (`api_error_response` — logged even if you don't pass `raise_on_error`, which only controls whether it's *also* raised), request timeouts/connection errors, WebSocket authentication/connect/subscribe/unsubscribe failures, exhausted reconnect attempts, and circuit breaker opening. |

Response bodies over 4KB get a size summary **plus** a preview (the first 1000
characters of the raw response text) instead of being logged in full, so one
large response (e.g. the scrip master download, a big `option_chain()`/
`historical_data()` payload) can't bloat the log file while an error message
near the start of the body stays visible for debugging — the object returned
to your code is never truncated, only what gets written to the log.

## What every entry carries

Every entry — including ones logged by third-party libraries the SDK depends on, like
`httpx` — carries:

- `timestamp` (always IST/Asia-Kolkata, regardless of the host process's own
  timezone), `level`, `logger` name
- `environment` (`"prod"`/`"uat"`, taken from the `NeoAPI(environment=...)` your
  client was actually constructed with, once it's been created — `"unknown"` before
  that, or if none was ever created in this process)

**Request/response headers are not logged at all** — `api_request_start` records
method, URL, query params, and body, but never headers, so an actual
`Authorization` header value never reaches the log file in the first place.
Credential-shaped *field* names that do appear in a logged body or params dict
(passwords, `consumer_key`/`consumer_secret`, `bearer_token`/`edit_token`/
`view_token`/`access_token`, `sid`, `mpin`, OTP/TOTP, `auth`, etc.) are
automatically masked before anything is written. **Instrument identifiers are
not masked** — `exchange_token` (`quotes()`) and `instrument_token` (SFeed
subscribe/unsubscribe and per-message logs) are logged in full, since they're
not credentials and masking them made feed/quote logs useless for tracing a
specific instrument.

## No stdout printing from the library

The SDK never prints warnings/errors to stdout directly — everything goes through
structured logging as described above.

## Troubleshooting an issue? Share the log file

If you run into an issue — a failed order, an unexpected disconnect, a REST error
that's hard to reproduce — enable file logging at `INFO` before you reproduce it, then
share the resulting `logs/neo-api-client.log` with support. It carries the full
request/response detail (REST and WebSocket) needed to diagnose the problem, with
sensitive fields already masked (see [What every entry carries](#what-every-entry-carries)) —
no need to redact anything yourself before sharing.

```python
from neo_api_client.logger import setup_logging

setup_logging(file_level="INFO")
```

Then reproduce the issue and attach `logs/neo-api-client.log` (or the specific day's
rotated file) when you:

- Open a [GitHub Issue](https://github.com/Kotak-Neo/kotak-neo-python/issues)
- Email support@kotakneo.com

Include the approximate time the issue occurred so the relevant entries are easy to
find.
