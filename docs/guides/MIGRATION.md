# Migration Guide — v2.0.2 → v2.2.5

This guide helps you upgrade the **Kotak Neo Python SDK** (`neo_api_client`) from
**v2.0.2** to **v2.2.5**.

The package import name is unchanged (`neo_api_client`), so your `import`
statements keep working. However, several APIs changed in ways that **require
code updates** — most importantly the WebSocket client (now async/await), error
handling (now raises exceptions), and stricter order-parameter validation.

> **TL;DR of what you must change**
> 1. WebSocket code must move from callbacks to `async`/`await`.
> 2. Order placement rejects `CO`/`BO` products, `CDS`/`cde_fo` exchange segment, and non-`DAY`/`IOC` validity.
> 3. Errors are now raised as exceptions (wrap calls in `try/except`).
> 4. A few methods were removed (`cancel_cover_order`, `cancel_bracket_order`).

---

## 1. Installation & requirements

| | v2.0.2 | v2.2.5 |
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

The TOTP two-step flow is the same in both versions:

```python
from neo_api_client import NeoAPI

client = NeoAPI(consumer_key="your-consumer-key", environment="prod")
client.totp_login(mobile_number="+919876543210", ucc="YOUR_UCC", totp="123456")
client.totp_validate(mpin="1234")
```

Points to verify when upgrading:

- **Use the keyword `mobile_number`** (with underscore). Some older doc snippets
  showed `mobilenumber` (one word); that was never the real parameter name and
  raises `TypeError`.
- The legacy `login()` / `generateOTP()` / `session_2fa()` password-based flow and
  `customer_key` / `customer_secret` do **not** exist. Use `consumer_key` +
  `totp_login` + `totp_validate` only.
- `environment="prod"` is the default and correct value for all customers.
- **Blank/missing fields are rejected client-side.** `totp_login()`/`totp_validate()`
  reject a blank/missing `mobile_number`/`ucc`/`totp`/`mpin` before sending anything,
  using the same error shape the backend itself returns for this case, e.g.:
  `{"error": [{"code": "400", "message": "Missing required field 'MobileNumber'"}]}`.

---

## 3. Order placement & modification — stricter validation

The SDK now validates order parameters **before** sending the request and raises
a clear error for invalid input, instead of forwarding it to the exchange.

### 3.1 Product type — only `CNC`, `NRML`, `MIS`, `MTF`

```python
# v2.2.5: allowed product values
client.place_order(..., product="CNC")   # or "NRML", "MIS", or "MTF"
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

### 3.2 Exchange segment — currency derivatives (`CDS`/`cde_fo`) no longer accepted

`place_order` now rejects `CDS`/`cds`/`cde_fo`. The allowed values are
`NSE`/`nse_cm`, `BSE`/`bse_cm`, `NFO`/`nse_fo`, `BFO`/`bse_fo`, `BCD`/`bcs-fo`,
and `MCX`/`mcx_fo`. If your v2.0.2 code placed orders on the currency
derivatives segment, that path is removed.

`modify_order` no longer takes an `exchange_segment` parameter at all (see
§3.6) — it always uses the default validity set (§3.3) and whichever segment
the order was originally placed on at the exchange.

### 3.3 Validity — per exchange segment (`place_order` only)

`place_order` validates validity against the exchange segment:

| Segment | Allowed validity |
|---|---|
| `nse_cm`, `bse_cm`, `nse_fo`, `bse_fo` | `DAY`, `IOC` |
| `mcx_fo` | `DAY` only |

`modify_order` has no `exchange_segment` parameter, so it always checks
validity against the default set (`DAY`, `IOC`), regardless of which segment
the order lives on.

`GTC`, `EOS`, and `GTD` are **no longer accepted** and raise a validation error.

### 3.4 Price — must be positive for `L`/`SL` orders

```python
# v2.2.5: price=0 is now rejected for Limit and Stop-Loss-Limit orders
client.place_order(..., order_type="L", price="0")   # raises ApiValueError
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

### 3.5 Blank / invalid inputs are rejected

Mandatory fields (`exchange_segment`, `product`, `price`, `order_type`,
`quantity`, `validity`, `trading_symbol`, `transaction_type`) must be non-blank
and well-formed (numeric price, positive-integer quantity, …). Blank or malformed
values now raise a validation error rather than being silently sent.

### 3.6 `modify_order` — `instrument_token`/`exchange_segment`/`trading_symbol`/`transaction_type` removed

`modify_order()` no longer accepts `instrument_token`, `exchange_segment`,
`trading_symbol`, or `transaction_type` — they were never mandatory (the
backend only requires `order_id`, `price`, `order_type`, `quantity`, and
`validity`), and the "quick-modify" vs. "order-id-only" distinction they
existed for is gone. Drop them from any call:

```python
# Before (v2.2.5, "quick-modify" path)
client.modify_order(
    order_id="250101000000001", price="1450", order_type="L", quantity="1",
    validity="DAY", instrument_token="11536", exchange_segment="nse_cm",
    product="CNC", trading_symbol="RELIANCE-EQ", transaction_type="B",
)

# Now
client.modify_order(
    order_id="250101000000001", price="1450", order_type="L", quantity="1",
    validity="DAY", product="CNC",
)
```

`product` is still accepted (optional; exact canonical codes only — see §3.1).

### 3.7 `modify_order` — optional exchange-rejection check (`isVerify`)

Order modification is acknowledged asynchronously: the server returns
`stat: "Ok"` when it *accepts* the request, but the exchange may reject it moments
later (e.g. a price outside the allowed band), which appears on the order book
afterwards. Pass `isVerify=True` to have the SDK re-check the order book and
return a failure if the modification was rejected:

```python
result = client.modify_order(
    order_id="250101000000001",
    price="1450",
    order_type="L",
    quantity="1",
    validity="DAY",
    isVerify=True,   # new in 2.2.x — confirm the final outcome
)
```

### 3.8 AMO orders

Pass `amo="YES"` to place/modify/cancel an After-Market Order. The `am` flag is
always sent (defaults to `"NO"`).

---

## 4. Error handling — exceptions instead of silent dicts

**This is the most impactful behavioral change.** In v2.0.2 many methods swallowed
errors and returned dicts like `{"Error": <exception>}` or
`{"Error Message": "Complete the 2fa process ..."}`, so `try/except` around calls
did nothing. In v2.2.5 the SDK raises a typed exception hierarchy.

```python
from neo_api_client import (
    NeoAPIException,      # base
    AuthenticationError,
    ValidationError,
    RateLimitError,
    NetworkError,
    OrderError,
)

try:
    client.place_order(
        exchange_segment="nse_cm", product="CNC", price="1500",
        order_type="L", quantity="1", validity="DAY",
        trading_symbol="RELIANCE-EQ", transaction_type="B",
    )
except ValidationError as e:
    print("Invalid order parameters:", e)
except AuthenticationError:
    print("Session invalid — re-login")
except NeoAPIException as e:
    print("API error:", e)
```

**Action:** review any code that inspected `response["Error"]` and switch to
`try/except`.

---

## 5. Removed methods

| Removed in v2.2.x | Replacement |
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
`on_error`, then call `subscribe`). v2.2.5 uses a modern **async/await** client
with typed Pydantic messages.

### 6.1 Market data (LTP, option chain, depth)

**Before (v2.0.2):**

```python
def on_message(message):
    print(message)

client.on_message = on_message
client.on_error = lambda e: print(e)
client.subscribe(
    instrument_tokens=[{"instrument_token": "11536", "exchange_segment": "nse_cm"}]
)
```

**After (v2.2.5):**

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
                print(msg.data.order_no, msg.data.order_status)
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
- **Structured logging.** Configure via `NEO_LOG_LEVEL` / `NEO_LOG_JSON`
  environment variables.
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

---

## 8. Upgrade checklist

- [ ] Bump Python to 3.10+ and `pip install --upgrade kotakneoapi`.
- [ ] Remove any exact transitive pins carried over from v2.0.2.
- [ ] Confirm auth uses `consumer_key` + `totp_login(mobile_number=...)` + `totp_validate(mpin=...)`.
- [ ] Replace `product="CO"/"BO"`, `exchange_segment="CDS"/"cde_fo"`, and `validity="GTC"/"EOS"/"GTD"` usages.
- [ ] Replace `price="0"`/blank on `L`/`SL` orders with a real limit price.
- [ ] Wrap order/API calls in `try/except` for the new exception hierarchy.
- [ ] Rewrite WebSocket code to the async `create_websocket()` / `create_order_feed()` model.
- [ ] Replace `subscribe_to_orderfeed` and any cover/bracket cancel calls.
- [ ] (Optional) Add `isVerify=True` to `modify_order` where you need confirmed outcomes.
- [ ] Drop `segment`/`exchange`/`product` from `limits()` and `market_protection` from `place_order`/`modify_order` calls.
- [ ] Drop the bracket/cover-order-only `place_order()` params (`pf`, `tag`, `scrip_token`, `square_off_type`, `stop_loss_type`, `stop_loss_value`, `square_off_value`, `last_traded_price`, `trailing_stop_loss`, `trailing_sl_value`).
- [ ] Drop `instrument_token`, `exchange_segment`, `trading_symbol`, and `transaction_type` from `modify_order()` calls.
- [ ] Replace `trade_report(order_id=...)` with `order_report(order_id=...)` for single-order lookups.
- [ ] Replace `margin_required()` `exchange_segment`/`order_type` aliases (e.g. `"NSE"`, `"Limit"`) with their exact canonical codes.

---

## Need help?

- **Full API reference:** [docs/functions/README.md](../functions/README.md)
- **WebSocket guide:** [docs/guides/websocket.md](./websocket.md)
- **Issues:** https://github.com/Kotak-Neo/kotak-neo-python/issues
