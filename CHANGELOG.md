# Changelog

All notable changes to this project are documented in this file.

## [3.0.12] - 2026-10-27

### New
- **`nse_com` (NSE Commodity) exchange segment support** — accepted by
  `place_order()`, `margin_required()`, `quotes()`, and `search_scrip()`.
  `place_order()` enforces `nse_com`-specific restrictions: `product` must
  be `MIS` or `NRML` (`CNC`/`MTF` rejected), and `order_type` must be `L`,
  `MKT`, or `SL` (`SL-M` rejected); `validity` accepts `DAY`/`IOC`, same as
  other cash segments. See
  [place_order.md](docs/functions/orders/place_order.md#parameters) and
  [margin_required.md](docs/functions/portfolio/margin_required.md).

### Fixes
- **UAT environment's `totp_login()`/`totp_validate()` were pointing to a
  non-working path** (`api/1.0/login/v6/totp/login`) — now correctly resolve
  to `login/1.0/tradeApiLogin`/`login/1.0/tradeApiValidate`, matching the
  working endpoint shape.
- **`search_scrip(exchange_segment="nse_com")` raised `ValueError`** when
  filtering by `expiry` (e.g. `time data "1483885800" doesn't match format
  "%d%b%Y"`). `nse_com` carries real expiry dates despite not using the
  `_fo` naming convention, but wasn't included in the segments whose
  `pExpiryDate` gets converted from the raw epoch-seconds value the backend
  sends. `nse_com` now gets its own `pExpiryDate` conversion, including a
  `nse_com`-specific ~10-year adjustment (not applied to any other segment,
  including `nse_fo`).

## [3.0.9] - 2026-10-15

### Changes
- `positions()` now calls `portfolio/v2/positions` (previously
  `quick/user/positions`), per a backend endpoint update — the response now
  includes an `ltp` field per position.

### Fixes
- **Order feed / SFeed could silently stop reconnecting after a disconnect**
  if a caller's `on_disconnect`/`on_error` callback raised — the exception
  propagated out of the internal reconnect loop, killing the background
  receive task with no further log output and no retry, while the caller's
  `async for` loop over the feed just ended quietly (no error surfaced).
  These callbacks are now exception-safe, matching `on_message`/`on_raw`
  (already guarded the same way): a callback bug degrades gracefully
  instead of silently stopping the feed.
- **Order feed / SFeed reconnect could falsely report failure (and burn
  through `max_reconnect_attempts`) even when the reconnect actually
  succeeded**, if a caller's `on_connect` callback raised. `on_connect()` is
  called after the socket is already open and the receive task already
  started, so letting it raise meant the internal reconnect loop's
  `await self.connect()` call looked like a failed attempt and retried
  against a connection that didn't need it — eventually exhausting
  `max_reconnect_attempts` and giving up for good, against what was actually
  a live connection. `on_connect` is now exception-safe too.
- **`async for message in ws:` (SFeed and order feed) ended the entire
  iteration on *any* disconnect, even a sub-second blip the SDK's own
  auto-reconnect would otherwise recover from transparently.** `__anext__()`
  checked `_connected` directly, which flips to `False` the instant a
  disconnect is detected — before the background reconnect has had any
  chance to retry. The iterator ending immediately looked identical to the
  server going down and the SDK giving up for good. `__anext__()` now only
  ends the iteration once reconnection is actually exhausted
  (`sfeed_reconnect_exhausted`/`orderfeed_reconnect_exhausted`) or `close()`
  was called explicitly — a disconnect that recovers in the background (the
  common case) is now invisible to the consumer, matching the documented
  "Auto-reconnect ... after a later drop" behavior.

### Enhancements
- `quotes()`, `expiries()`, `option_chain()`, `historical_data()` now surface any
  `Retry-After`/`X-RateLimit-*` response headers the backend Trade APIs send,
  under a `rateLimit` key on the returned dict — giving callers a concrete
  value to back off on after a `429`. Only added when the backend actually
  sends one of these headers; absent otherwise, so existing response shapes
  are unaffected.
- `orderfeed_disconnected`/`sfeed_disconnected` log events now include
  `close_code`/`close_reason` — the actual WebSocket close frame the server
  (or the connection itself) sent, giving a concrete answer to why a
  disconnect happened instead of just that one happened.
- `docs/scripts/migrate_from_v2.py` now also checks the **active environment**
  (not just your source files) for leftover files from a legacy
  `neo-api-client` install that was never uninstalled — see
  [Migration Guide §1.1](docs/guides/MIGRATION.md#11-package-coexistence-and-rollback).

### Docs
- `historical_data.md`, `expiries.md`, `option_chain.md` now document that
  these endpoints are backend-rate-limited (matching `quotes()`'s existing 25
  requests/second note) and how to read the new `rateLimit` field.
- `trade_report.md` now notes that the backend always returns an empty `tok`
  on this endpoint (unlike `order_report()`), and documents the workaround
  (match `nOrdNo` against `order_report()`, or resolve via `search_scrip()`).
- Each platform installation guide (Windows/macOS/Linux/local) now has a
  dedicated "Upgrading from the Legacy `neo-api-client` Package" section
  with the uninstall-then-install steps, not just a pointer from the
  installation overview page.

## [3.0.7] - 2026-09-15

### Fixes
- **Order feed / SFeed crash after running for hours** (`RecursionError: maximum
  recursion depth exceeded`) — both WebSocket clients' idle-timeout retry
  (`__anext__()`) and reconnect retry (`_handle_disconnect()`) used recursion
  instead of a loop, so a long-idle connection or a run of failed reconnect
  attempts would eventually blow the stack. Both are now implemented as loops,
  so the feed can run indefinitely through idle periods or extended outages
  without crashing.
- Fixed `totp_login()`/`totp_validate()`/`whatsmyip()` sending the **prod** API
  path even when `environment="uat"` — these previously hardcoded the prod
  endpoint path regardless of environment; they now resolve the correct
  UAT-specific path.

## [3.0.6] - 2026-09-05

> Covers everything since the last tagged release, `v3.0.1` (2026-08-17). Versions
> 3.0.2–3.0.5 were internal version bumps that were never tagged/released on their own.

### New Functions
- **`expiries()`, `option_chain()`, `historical_data()`** — new market-data endpoints
  (expiry dates, option/futures chains, historical candles), with full docs under
  `docs/functions/market_data/`.
- **`place_order(tag=...)`** — caller-defined marker for tracking an order, echoed back
  as `GuiOrdId` in `order_report()`/`trade_report()`.

### WebSocket
- **Market status / CAS support** on the SFeed — session open/close, pre-open, and Closing
  Auction Session (CAS) transition notifications, plus CAS reference (imbalance) data.
- New **Jupyter Notebook support**: install guide, a Jupyter compatibility CI workflow,
  and a smoke-test notebook.
- New **sync-integration guide** (`docs/guides/sync-integration.md`) for bridging the
  async SFeed/order-feed clients into synchronous, multi-process apps (Django/Flask
  behind gunicorn/uWSGI, Celery workers).

### Logging (significant overhaul)
- Structured JSON logging via `structlog`, with independently configurable console and
  rotating-file outputs (`NEO_LOG_LEVEL`, `NEO_LOG_FILE_ENABLED`/`PATH`/`LEVEL`).
- Large response bodies are size-capped in the log (with a preview) instead of bloating
  the log file; sensitive fields are auto-masked.
- Consolidated so each REST call now writes **one** log line instead of several — merged
  the separate "request start" and "success/error" events, and pinned `httpx`'s own
  internal logger to `WARNING` so it no longer duplicates every request in the log.
- `totp_login()`/`totp_validate()`'s function-result log now records only a status, not
  the full response (avoids repeating the auth token across two log lines).
- Our log handlers now attach to a dedicated `neo_api_client` logger instead of the root
  logger, and no longer propagate past it — so they can't collide with (and duplicate)
  whatever logging setup the host application itself uses.

### Dependencies
- Routine `ruff` version bumps via Dependabot (0.16.2 → 0.16.5).

## [3.0.1] - 2026-08-17

### Fixes
- `NEO_LOG_LEVEL` now defaults to `WARNING` instead of `INFO` — the SDK is
  quiet by default. Routine per-request tracing (`api_request_start`/
  `api_request_success`, `rest_client_initialized`, etc.) now logs at
  `DEBUG`, so only warnings and errors are visible unless you explicitly
  opt into more verbosity via `NEO_LOG_LEVEL=INFO` or `DEBUG`.
