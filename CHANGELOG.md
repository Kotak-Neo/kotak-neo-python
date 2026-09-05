# Changelog

All notable changes to this project are documented in this file.

## [3.0.5] - 2026-09-05

> Covers everything since the last tagged release, `v3.0.1` (2026-08-17). Versions
> 3.0.2–3.0.4 were internal version bumps that were never tagged/released on their own.

### New Functions
- **`expiries()`, `option_chain()`, `historical_data()`** — new market-data endpoints
  (expiry dates, option/futures chains, historical candles), with full docs under
  `docs/functions/market_data/`.
  - `historical_data()`'s `interval` now supports `D` (daily) and `W` (weekly) in
    addition to intraday intervals (`1min`…`60min`), each with documented date-range
    limits.
  - Like `quotes()`/`scrip_master()`, none of these three require `totp_validate()` —
    only `consumer_key` is required.
  - Historical data is not available for `mcx_fo` and `nse_com`.
- **`place_order(tag=...)`** — caller-defined marker for tracking an order, echoed back
  as `GuiOrdId` in `order_report()`/`trade_report()`.

### WebSocket
- **Market status / CAS support** on the SFeed — session open/close, pre-open, and Call
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

### Fixes
- Wire query param corrected to `instrument_type` (was `instrumentType`) for
  `expiries()`/`option_chain()`.
- `instrument_type` values corrected to lowercase (`option`/`fut`) in docs/examples —
  matches what the backend actually expects.
- Various documentation corrections: exchange enum lists (`nse_fo`/`bse_fo`/`mcx_fo`),
  `option_chain()`'s `count` parameter description, Postman collection `base_url`.

### Dependencies
- Routine `ruff` version bumps via Dependabot (0.16.2 → 0.16.5).

## [3.0.1] - 2026-08-17

Last previously tagged release.
