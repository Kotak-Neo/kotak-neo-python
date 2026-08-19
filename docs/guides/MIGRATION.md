# Migration Guide — v2.0.2 → v3.0.X

This guide helps you upgrade the **Kotak Neo Python SDK** (`neo_api_client`) from
**v2.0.2** to **v3.0.0**.

The package import name is unchanged (`neo_api_client`), so your `import`
statements keep working. However, several APIs changed in ways that **require
code updates** — most importantly the WebSocket client (now async/await) and
stricter order-parameter validation. Error handling is **largely unchanged**
(see §4) — this is easy to assume changed and it's worth reading that section
even if you skim the rest.

> **TL;DR of what you must change**
> 1. WebSocket code must move from callbacks to `async`/`await`.
> 2. Order placement rejects `CO`/`BO` products, generic/currency-derivatives exchange segments (only exact codes like `nse_cm`/`bse_fo` are accepted), order-type aliases like `"Limit"`/`"Market"` (only exact codes `L`/`MKT`/`SL`/`SL-M` are accepted), and non-`DAY`/`IOC` validity.
> 3. `NeoAPI(...)` — pass `consumer_key` and other args as **keywords**, not positionally: the parameter order changed and the `environment` default flipped from `"uat"` to `"prod"` (see §2).
> 4. A few methods were removed (`cancel_cover_order`, `cancel_bracket_order`); `place_order()`/`modify_order()`/`trade_report()`/`limits()` had parameters removed (see §5, §7).
> 5. Error handling for REST calls (`place_order`, `modify_order`, etc.) is **not** switching to exceptions — keep checking `if "Error" in result` (see §4).

Before going through this guide by hand, run the automated scanner below against
your codebase — it finds most of the issues covered in this document for you.

---

## 0. Automated scan: `docs/scripts/migrate_from_v2.py`

The SDK repo ships a read-only scanner that walks your project's `.py` files
looking for exactly the v2 → v3.0.0 breakages described in this guide —
removed methods and imports, dropped keyword arguments, unsafe positional
`NeoAPI(...)` construction, rejected `exchange_segment`/`product`/`order_type`/
`validity` alias literals (§3), `price="0"` on `L`/`SL` orders, and legacy
WebSocket callback usage (§6). It **never modifies your files**; it only
prints `file:line` findings so you can fix each one with full context.

```bash
# From a clone of kotak-neo-python
python docs/scripts/migrate_from_v2.py /path/to/your/project

# Or scan specific files
python docs/scripts/migrate_from_v2.py bot.py strategies/momentum.py
```

Example output:

```
[ERROR] bot.py:3: NeoAPI(...): Constructor positional order changed: v2 was
(environment, access_token, neo_fin_key, consumer_key); kotakneoapi is
(consumer_key, environment, access_token, neo_fin_key). ...
[ERROR] bot.py:21: cancel_cover_order(...): Removed in kotakneoapi. ...
[WARNING] bot.py:8: place_order(...): parameter(s) [stop_loss_value, tag] no
longer exist in kotakneoapi and will raise TypeError. ...

2 error(s), 1 warning(s) across 1 file(s).
```

The exit code is `1` if any error-level finding was reported, `0` otherwise —
suitable for a pre-migration CI check or a pre-commit gate while you're
migrating a large codebase incrementally.

The scanner checks the alias/removed-value rules in §3 (e.g. rejected `CO`/`BO`
products, order-type aliases like `"Limit"`) only when the value is a literal
string in the call itself — it can't see values built at runtime (f-strings,
variables, config lookups, values loaded from a file). It also doesn't verify
blank/malformed-input rejection (§3.6) or per-segment validity rules beyond the
literal alias list. Treat a clean scan as "no known mechanical breakages seen
in static analysis," not "fully migrated" — still read §3 and test against
`environment="uat"` before going live.

---

## 1. Installation & requirements

| | v2.0.2 | v3.0.0 |
|---|---|---|
| Python | 3.7+ | **3.10 – 3.14** |
| HTTP transport | `requests` | **`httpx` (HTTP/2)** |
| Dependency pins | exact (`urllib3==1.26.14`, …) | loose ranges |

```bash
pip install --upgrade kotakneoapi
```

If you previously pinned transitive packages (e.g. `urllib3`, `certifi`) to match
the old SDK's exact pins, remove those pins — the new SDK uses loose ranges and
`httpx`, and old pins may now conflict.

---

## 2. Authentication (unchanged in shape, but confirm your flow)

The TOTP two-step flow (`totp_login` → `totp_validate`) is the same in both
versions — but **`NeoAPI(...)`'s constructor changed in a way that silently
breaks positional calls.** Always pass its arguments as keywords:

```python
from neo_api_client import NeoAPI

client = NeoAPI(consumer_key="your-consumer-key", environment="prod")
client.totp_login(mobile_number="+919876543210", ucc="YOUR_UCC", totp="123456")
client.totp_validate(mpin="1234")
```

### ⚠️ `NeoAPI(...)` parameter order changed — silent breakage risk

| | v2.0.2 | v3.x.x |
|---|---|---|
| Parameter order | `environment, access_token, neo_fin_key, consumer_key` | `consumer_key, environment, access_token, neo_fin_key` |
| `environment` default | `"uat"` | `"prod"` |

If your v2.0.2 code constructed the client **positionally** — e.g.
`NeoAPI("prod", None, None, "my-consumer-key")` — upgrading will **not**
raise an error. It will silently assign `"prod"` to `consumer_key` and drop
`"my-consumer-key"` into an unused slot, and authentication will fail with no
obvious cause. Switch to keyword arguments (`NeoAPI(consumer_key=..., environment=...)`)
before upgrading, and verify: if you previously relied on the `"uat"` default
by omitting `environment=` entirely, you're now defaulting to **production**.

Other points to verify when upgrading:

- **Use the keyword `mobile_number`** (with underscore). Some older doc snippets
  showed `mobilenumber` (one word); that was never the real parameter name and
  raises `TypeError`.
- The legacy `login()` / `generateOTP()` / `session_2fa()` password-based flow and
  `customer_key` / `customer_secret` do **not** exist in either version — grepping
  v2.0.2's source shows they were never actually implemented, only referenced in
  its docstring/demo script. If you copied from those, switch to `consumer_key` +
  `totp_login` + `totp_validate`.
- **Blank/missing fields are rejected client-side.** `totp_login()`/`totp_validate()`
  reject a blank/missing `mobile_number`/`ucc`/`totp`/`mpin` before sending anything,
  using the same error shape the backend itself returns for this case, e.g.:
  `{"error": [{"code": "400", "message": "Missing required field 'MobileNumber'"}]}`.
  This is additive (v2.0.2 had no such guard) — if a network failure happens
  during `totp_login`/`totp_validate` itself (not a blank-field case), an
  `ApiException` still propagates uncaught, unchanged from v2.0.2 (see §4).

---

## 3. Order placement & modification — stricter validation

The SDK now validates order parameters **before** sending the request and raises
a clear error for invalid input, instead of forwarding it to the exchange.

### 3.1 Product type — only `CNC`, `NRML`, `MIS`, `MTF`

```python
# v3.0.0: allowed product values
client.place_order(..., product="CNC")  # or "NRML", "MIS", or "MTF"
```

`CO` (Cover Order) and `BO` (Bracket Order) are **no longer accepted** by
`place_order` and now raise a validation error. If your v2.0.2 code placed
cover/bracket orders, that path is removed (see §5).

The bracket/cover-order-only parameters `pf`, `tag`, `scrip_token`,
`square_off_type`, `stop_loss_type`, `stop_loss_value`, `square_off_value`,
`last_traded_price`, `trailing_stop_loss`, and `trailing_sl_value` have been
removed from `place_order()` along with that order type. Drop them from any
call — passing them now raises `TypeError` (unexpected keyword argument)
instead of being silently ignored.

### 3.2 Exchange segment — only the exact canonical codes are accepted

`place_order` now accepts **only** the exact canonical segment codes:
`nse_cm`, `bse_cm`, `nse_fo`, `bse_fo`, `mcx_fo`. Generic aliases like `NSE`,
`BSE`, `NFO`, `BFO`, `MCX` are **no longer resolved** — they now raise a
validation error, because they're ambiguous about which specific segment an
order applies to (e.g. `BSE` could mean the cash segment `bse_cm` or the F&O
segment `bse_fo`; silently resolving it to `bse_cm` could route an order to
the wrong segment). Currency derivatives (`CDS`/`cds`/`cde_fo`) and BSE
currency derivatives (`BCD`/`bcd`/`bcs-fo`) aren't accepted at all, under any
spelling — they aren't supported segments. If your v2.0.2 code used any of
these generic aliases, switch to the exact segment code:

```python
# Before — no longer accepted
client.place_order(..., exchange_segment="BSE")

# Now — use the exact segment
client.place_order(..., exchange_segment="bse_cm")  # or "bse_fo"
```

`modify_order` no longer takes an `exchange_segment` parameter at all (see
§3.7) — it always uses the default validity set (§3.4) and whichever segment
the order was originally placed on at the exchange.

### 3.3 Order type — only `L`, `MKT`, `SL`, `SL-M`

`place_order` and `modify_order` now accept **only** the exact canonical
order-type codes: `L`, `MKT`, `SL`, `SL-M`. Aliases like `Limit`, `Market`,
`Stop loss limit`, `Stop loss market` are **no longer resolved** — they now
raise a validation error. Multi-leg order types (`SP`/`Spread`, `2L`/`Two Leg`,
`3L`/`Three leg`) are also no longer accepted by either method. If your
v2.0.2 code used any of these, switch to the exact code:

```python
# Before — no longer accepted
client.place_order(..., order_type="Limit")

# Now — use the exact code
client.place_order(..., order_type="L")
```

### 3.4 Validity — per exchange segment (`place_order` only)

`place_order` validates validity against the exchange segment:

| Segment | Allowed validity |
|---|---|
| `nse_cm`, `bse_cm`, `nse_fo`, `bse_fo` | `DAY`, `IOC` |
| `mcx_fo` | `DAY` only |

`modify_order` has no `exchange_segment` parameter, so it always checks
validity against the default set (`DAY`, `IOC`), regardless of which segment
the order lives on.

`GTC`, `EOS`, and `GTD` are **no longer accepted** and raise a validation error.

### 3.5 Price — must be positive for `L`/`SL` orders

```python
# v3.0.0: price=0 is now rejected for Limit and Stop-Loss-Limit orders
client.place_order(..., order_type="L", price="0")  # raises ApiValueError
client.place_order(..., order_type="L", price="1500")  # OK — a real limit price
client.place_order(..., order_type="MKT", price="0")  # still OK — market orders ignore price
```

`price=0` (or blank) previously reached the exchange for `L` (Limit) and `SL`
(Stop-Loss Limit) orders, which has been observed to make the exchange silently
substitute a default price instead of rejecting the order — resulting in an
unintended fill at a nonsense price. The SDK now rejects `price=0` client-side
for `L`/`SL` order types. `MKT` and `SL-M` orders are unaffected — they
legitimately execute at the prevailing market price, so `price=0` remains valid
there. The same rule applies to `modify_order`.

### 3.6 Blank / invalid inputs are rejected

Mandatory fields (`exchange_segment`, `product`, `price`, `order_type`,
`quantity`, `validity`, `trading_symbol`, `transaction_type`) must be non-blank
and well-formed (numeric price, positive-integer quantity, …). Blank or malformed
values now raise a validation error rather than being silently sent.

### 3.7 `modify_order` — `instrument_token`/`exchange_segment`/`trading_symbol`/`transaction_type`/`product`/`dd`/`filled_quantity` removed

`modify_order()` no longer accepts `instrument_token`, `exchange_segment`,
`trading_symbol`, `transaction_type`, `product`, `dd`, or `filled_quantity` —
none of them are required by the backend for a modify request, and the
"quick-modify" vs. "order-id-only" distinction the first four existed for is
gone. Drop them from any call:

```python
# Before (v3.0.0, "quick-modify" path)
client.modify_order(
    order_id="250101000000001",
    price="1450",
    order_type="L",
    quantity="1",
    validity="DAY",
    instrument_token="11536",
    exchange_segment="nse_cm",
    product="CNC",
    trading_symbol="RELIANCE-EQ",
    transaction_type="B",
)

# Now
client.modify_order(
    order_id="250101000000001",
    price="1450",
    order_type="L",
    quantity="1",
    validity="DAY",
)
```

### 3.8 `modify_order` does not accept `isVerify` — don't copy it from `cancel_order`

`modify_order()` never had an `isVerify` parameter in v2.0.2 either — that
flag only ever existed on `cancel_order()`/`cancel_cover_order()`/
`cancel_bracket_order()` (see §5), triggering an order-book re-check before
cancelling. If you copy-pasted `isVerify=True` from a `cancel_order()` call
into a `modify_order()` call, drop it — it raises `TypeError` in both
versions, this isn't a v3.0.0 behavior change. `modify_order()` now always
returns the raw OMS acknowledgement (`stat: "Ok"` on acceptance); confirm the
final state via the order feed or order history.

```python
# Invalid in both v2.0.2 and v3.0.0 — isVerify was never a modify_order() param
client.modify_order(
    order_id="250101000000001",
    price="1450",
    order_type="L",
    quantity="1",
    validity="DAY",
    isVerify=True,
)

# Correct
client.modify_order(
    order_id="250101000000001",
    price="1450",
    order_type="L",
    quantity="1",
    validity="DAY",
)
```

### 3.9 AMO orders

Pass `amo="YES"` to place/modify/cancel an After-Market Order. The `am` flag is
always sent (defaults to `"NO"`).

---

## 4. Error handling — mostly unchanged; don't switch to `try/except` for REST calls

**This is not the sweeping change it might look like.** `place_order()`,
`modify_order()`, `cancel_order()`, `order_report()`, `order_history()`,
`trade_report()`, `positions()`, `holdings()`, `margin_required()`, `limits()`,
`scrip_master()`, `search_scrip()`, `logout()`, and `whatsmyip()` all still
catch their own errors internally and return a dict — exactly like v2.0.2:

```python
result = client.place_order(
    exchange_segment="nse_cm",
    product="CNC",
    price="1500",
    order_type="Limit",  # invalid — only exact codes L/MKT/SL/SL-M are accepted (§3.3)
    quantity="1",
    validity="DAY",
    trading_symbol="RELIANCE-EQ",
    transaction_type="B",
)
# result == {"Error": ApiValueError("Invalid order type. Allowed values are L, MKT, SL, SL-M.")}
# No exception was raised — place_order() never raises for input-validation or
# network failures. Keep checking the response, don't wrap the call in try/except:
if "Error" in result or "error" in result:
    print("Order failed:", result)
```

**What actually changed:** the checks that produce that `{"Error": ...}` dict
got stricter (§3) and a couple of methods gained new failure dicts (e.g. the
`stCode: 1021` / `status_code: 400` shape on an already-complete order —
see [modify_order.md](../functions/orders/modify_order.md)) — but the *shape*
of a failure (a dict with an `"Error"`/`"error"`/`"Error Message"` key) is
the same as v2.0.2 for every method above. **Action:** if your v2.0.2 code
checked `if "Error" in response:`, no change is needed here.

### Where exceptions genuinely are raised

- **`totp_login()` / `totp_validate()`** — a network-level failure (e.g. the
  host is unreachable) raises `ApiException` **uncaught**, in both v2.0.2 and
  v3.x.x. This is the one place in the REST API surface where wrapping the
  call in `try/except ApiException` is warranted:

  ```python
  from neo_api_client import NeoAPI
  from neo_api_client.exceptions import ApiException

  try:
      client.totp_login(mobile_number="+919876543210", ucc="YOUR_UCC", totp="123456")
  except ApiException as e:
      print("Network/API error during login:", e)
  ```

  Note `ApiException` is a plain `Exception` subclass, not part of the
  `NeoAPIException` hierarchy below — `except NeoAPIException` will **not**
  catch it.

- **The async WebSocket clients** (`SFeedWebSocket`, `OrderFeedWebSocket` —
  see §6) do raise real exceptions: `AuthenticationError`, `ConnectionError`,
  and friends from the typed hierarchy below. This is new in v3.0.x, since
  the WebSocket client itself is new.

- **The optional rate limiter** (off by default; only active if you construct
  the client with `enable_rate_limiting=True`) raises `TimeoutError` when a
  request can't get a token in time.

The full typed hierarchy still exists and is exported for these cases:

```python
from neo_api_client import (
    NeoAPIException,  # base
    AuthenticationError,
    ValidationError,
    RateLimitError,
    NetworkError,
    OrderError,
)
```

Use it around WebSocket connect/subscribe calls, not around `place_order()`
and friends.

---

## 5. Removed methods

| Removed in v3.0.x | Replacement |
|---|---|
| `client.subscribe(...)` | `client.create_websocket()` → `ws.subscribe_scrips(...)` (see §6) |
| `client.un_subscribe(...)` | `ws.unsubscribe_scrips(...)` |
| `client.subscribe_to_orderfeed()` | `client.create_order_feed()` (see §6.2) |
| `client.cancel_cover_order(...)` | *(removed — cover/bracket products no longer supported)* |
| `client.cancel_bracket_order(...)` | *(removed)* |

Calling `subscribe` / `un_subscribe` / `subscribe_to_orderfeed` now raises
`NotImplementedError` with a message pointing to the new API.

---

## 6. WebSocket — from callbacks to async/await

The biggest code change. v2.0.2 used a callback model (assign `on_message`,
`on_error`, then call `subscribe`). v3.0.0 uses a modern **async/await** client
with typed Pydantic messages.

### 6.1 Market data (LTP, option chain, depth)

**Before (v2.0.2):**

```python
def on_message(message):
    print(message)


client.on_message = on_message
client.on_error = lambda e: print(e)
client.subscribe(instrument_tokens=[{"instrument_token": "11536", "exchange_segment": "nse_cm"}])
```

**After (v3.0.0):**

```python
import asyncio
from neo_api_client.websocket.feed import WsToken, SFeedScrip


async def main():
    async with client.create_websocket() as ws:
        await ws.subscribe_scrips([WsToken("nse_cm", "11536")])
        async for message in ws:
            if isinstance(message, SFeedScrip):
                print(message.trading_symbol, message.last_traded_price)


asyncio.run(main())
```

Key differences:

- **Typed messages.** You receive `SFeedScrip` / `SFeedScripLite` / `SFeedIndex` /
  `SFeedMarketStatus` objects with named attributes (e.g. `last_traded_price`),
  instead of dicts with cryptic 2-letter keys (`ltp`, `tbq`, …). Call
  `message.model_dump()` for a dict.
- **`trading_symbol` included.** Each message carries a human-readable
  `trading_symbol` (resolved from the subscribe acknowledgement) alongside
  `exchange_segment` and `instrument_token`.
- **Subscribe methods by data level:** `subscribe_scrips` (touch line),
  `subscribe_scrips_lite`, `subscribe_depth`, `subscribe_full_depth`,
  `subscribe_index` — each with a matching `unsubscribe_*`.
- **Indices vs. stocks/contracts:** use `subscribe_index(...)` for indices and
  `subscribe_scrips(...)` for stocks and contracts.
- **Prices are pre-scaled** by the per-exchange divider before you receive them.

Full reference: **[SFeed WebSocket Guide](./websocket.md)**.

### 6.2 Order & position feed

**Before:** `client.subscribe_to_orderfeed()` (callback).

**After:**

```python
import asyncio
from neo_api_client.websocket.orderfeed import OrderUpdate, PositionUpdate


async def main():
    async with client.create_order_feed() as feed:
        async for msg in feed:
            if isinstance(msg, OrderUpdate):
                print(msg.data.order_id, msg.data.order_status)
            elif isinstance(msg, PositionUpdate):
                print(msg.data.symbol)


asyncio.run(main())
```

See **[Order Feed](../functions/websocket/order_feed.md)**.

---

## 7. Other notable changes

- **HTTP/2 transport.** REST calls run over HTTP/2 (via `httpx`) with automatic
  HTTP/1.1 fallback. No code change required; response objects are `httpx.Response`
  (use `.reason_phrase` instead of `.reason` if you accessed it directly).
- **`order_report(order_id=...)`.** Fetches a single order by number
  (`/quick/user/orders/<order_no>`); omit `order_id` for the full order book.
- **`whatsmyip()`.** New method returning the client's outbound IP as seen by the
  server (useful for IP-whitelisting).
- **No stdout printing from the library.** The old SDK printed warnings/errors to
  stdout; the new SDK uses structured logging.
- **Structured logging.** Quiet by default (`NEO_LOG_LEVEL` defaults to
  `WARNING`, so routine per-request tracing stays silent) — set
  `NEO_LOG_LEVEL=INFO` or `DEBUG` for more verbosity. Also configurable via
  `NEO_LOG_JSON`.
- **Rotating log file, on by default, covers REST *and* WebSocket.**
  Warnings and errors — including WebSocket connect failures, disconnects,
  reconnect attempts, authentication failures, and subscription errors for
  both `SFeedWebSocket` and `OrderFeedWebSocket`, not just REST calls — are
  written to `logs/neo-api-client.log` (relative to your working directory),
  rotated daily with 7 days retained. Independent of the console level.
  Configure via `NEO_LOG_FILE_ENABLED` (set to `false` to disable),
  `NEO_LOG_FILE_PATH`, `NEO_LOG_FILE_LEVEL`, and `NEO_LOG_FILE_BACKUP_COUNT`.
- **Programmatic control via `setup_logging(...)`.** Both `level` (console)
  and `file_level` (file) also accept `"NOLOG"` to disable that output
  entirely — e.g. `setup_logging(file_level="NOLOG")` stops file logging,
  independent of the console. Call it directly (`from neo_api_client.logger
  import setup_logging`) to reconfigure at runtime instead of via env vars;
  each call fully replaces the previous configuration rather than adding to
  it.
- **`limits()` takes no parameters.** It always requests limits across all
  segments, exchanges, and products. If you called `limits(segment=..., exchange=..., product=...)`,
  drop those arguments — `client.limits()` now covers everything in one call.
- **`place_order()`/`modify_order()` no longer accept `market_protection`.**
  It's always sent as `"0"`. Drop the argument if you were passing it.
- **`trade_report()` no longer accepts `order_id`.** Fetching the trade report
  filtered by a single order ID isn't backend-supported — it always returns
  the full trade list now. To look up a single order's status, use
  `order_report(order_id=...)` instead.
- **`margin_required()` — `exchange_segment`/`order_type` aliases no longer
  accepted.** Only the exact canonical codes are accepted: `nse_cm`, `bse_cm`,
  `nse_fo`, `bse_fo`, `mcx_fo` for `exchange_segment`, and `L`, `MKT`, `SL`,
  `SL-M` for `order_type`. Aliases like `"NSE"`/`"MCX"` or `"Limit"`/`"Market"`
  now raise a validation error instead of being silently resolved.
- **WebSocket clients now retry the initial `connect()` on failure.**
  `SFeedWebSocket`/`OrderFeedWebSocket` (and `create_websocket()`/
  `create_order_feed()`) previously raised `ConnectionError` immediately if
  the very first attempt to open the socket failed. They now retry up to
  `max_connect_retries` times (default `3`), waiting `reconnect_delay`
  seconds between attempts, before raising. This is separate from the
  existing post-connect auto-reconnect (`max_reconnect_attempts`), which
  only applies after a connection has already succeeded once. If your code
  depended on an immediate failure (e.g. a test that mocks a single
  connect failure), pass `max_connect_retries=0` to restore the old
  fail-fast behavior.

---

## 8. Upgrade checklist

- [ ] Run `python docs/scripts/migrate_from_v2.py <your project>` and work through its findings (see §0).
- [ ] Bump Python to 3.10+ and `pip install --upgrade kotakneoapi`.
- [ ] Remove any exact transitive pins carried over from v2.0.2.
- [ ] Confirm auth uses `consumer_key` + `totp_login(mobile_number=...)` + `totp_validate(mpin=...)`.
- [ ] Pass `NeoAPI(...)` arguments as **keywords**, not positionally — the parameter order changed and `environment` now defaults to `"prod"` instead of `"uat"` (see §2).
- [ ] Replace `product="CO"/"BO"`, `exchange_segment="CDS"/"cde_fo"/"BCD"/"bcs-fo"`, generic segment aliases (`NSE`/`BSE`/`NFO`/`BFO`/`MCX`), order-type aliases (`"Limit"`/`"Market"`/`"Stop loss limit"`/`"Stop loss market"`/`"SP"`/`"2L"`/`"3L"`), and `validity="GTC"/"EOS"/"GTD"` usages in `place_order()`/`modify_order()`.
- [ ] Replace `price="0"`/blank on `L`/`SL` orders with a real limit price.
- [ ] **Do not** wrap `place_order`/`modify_order`/`cancel_order`/etc. in `try/except` expecting exceptions — they still return `{"Error": ...}` dicts, unchanged from v2.0.2 (see §4). Only wrap `totp_login`/`totp_validate` (may raise `ApiException` on network failure) and the WebSocket clients (raise the typed exception hierarchy).
- [ ] Rewrite WebSocket code to the async `create_websocket()` / `create_order_feed()` model.
- [ ] Replace `subscribe_to_orderfeed` and any cover/bracket cancel calls.
- [ ] Drop `segment`/`exchange`/`product` from `limits()` and `market_protection` from `place_order`/`modify_order` calls.
- [ ] Drop the bracket/cover-order-only `place_order()` params (`pf`, `tag`, `scrip_token`, `square_off_type`, `stop_loss_type`, `stop_loss_value`, `square_off_value`, `last_traded_price`, `trailing_stop_loss`, `trailing_sl_value`).
- [ ] Drop `instrument_token`, `exchange_segment`, `trading_symbol`, `transaction_type`, `product`, `dd`, and `filled_quantity` from `modify_order()` calls.
- [ ] Don't pass `isVerify` to `modify_order()` — it was never a valid parameter there in either version (it only exists on `cancel_order()`/`cancel_cover_order()`/`cancel_bracket_order()`, see §3.8).
- [ ] Replace `trade_report(order_id=...)` with `order_report(order_id=...)` for single-order lookups.
- [ ] Replace `margin_required()` `exchange_segment`/`order_type` aliases (e.g. `"NSE"`, `"Limit"`) with their exact canonical codes.

---

## Need help?

- **Automated migration scanner:** [docs/scripts/migrate_from_v2.py](../scripts/migrate_from_v2.py) (see §0)
- **Full API reference:** [docs/functions/README.md](../functions/README.md)
- **WebSocket guide:** [docs/guides/websocket.md](./websocket.md)
- **Issues:** https://github.com/Kotak-Neo/kotak-neo-python/issues
