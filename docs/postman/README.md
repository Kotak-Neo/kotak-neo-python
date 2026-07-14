# Postman Collection — Kotak Neo Trading APIs

A Postman collection mirroring the REST endpoints (and WebSocket reference stubs)
used by the `kotak-neo-python` SDK, for manual testing.

## Files

| File | Purpose |
|------|---------|
| `Kotak-Neo-API.postman_collection.json` | The collection (Auth, Orders, Portfolio, Market Data, WebSocket) |
| `Kotak-Neo-PROD.postman_environment.json` | Environment with the variables to fill in |

## Import

1. Open Postman → **Import** → drop both JSON files.
2. Select the **Kotak Neo - PROD** environment (top-right).
3. Fill in these variables (Environment → edit):
   - `consumer_key` — token from Kotak Neo app → Invest → Trade API
   - `mobile_number` — `+91XXXXXXXXXX`
   - `ucc` — your UCC
   - `totp` — current 6-digit code from your authenticator app
   - `mpin` — your trading MPIN

## Run order

1. **Auth → 1. TOTP Login** — captures `view_token` + `sid` automatically.
2. **Auth → 2. TOTP Validate (MPIN)** — captures `edit_token`, `edit_sid`, and
   the trading `base_url` automatically.
3. Any request under **Orders / Portfolio / Market Data** now works.
   - **Place Order** captures the returned `order_id`, so **Modify / Cancel /
     Order History / Order Book by ID** reuse it automatically.

> TOTP codes expire every ~30 seconds — refresh `totp` right before running Login.

## Request-body convention

Order/limits/margin endpoints send an **`x-www-form-urlencoded`** body with a
single **`jData`** field containing JSON (exactly as the SDK does). Edit the
`jData` value to change parameters. Key wire fields:

- Place: `es`(exchange_segment) `pc`(product: CNC/NRML/MIS/MTF) `pr`(price)
  `pt`(order_type) `qt`(quantity) `rt`(validity: DAY/IOC; mcx_fo=DAY only)
  `tp`(trigger) `ts`(trading_symbol) `tt`(B/S) `am`(amo YES/NO)
- Cancel: `on`(order number) `am`
- Modify: `no`(order number) + the same fields as place

## WebSocket

Postman's WebSocket support is **text-only** and does **not** decode the SFeed
binary market-data packets or automate the auth handshakes. The **WebSocket**
folder contains reference stubs documenting the URLs and frames:

- **SFeed market data** — `wss://sfeed.kotaksecurities.com/wsfeed`; subscribe with
  `{"event":"subscribeScrips","inputtoken":"nse_cm|11536","ack_symbol":true}`
- **Order & position feed** — `wss://<base_url host>/realtime`; send the raw
  handshake `{type:cn,Authorization:<edit_token>,Sid:<edit_sid>,src:WEB}`

For real streaming use the SDK (`create_websocket()` / `create_order_feed()`) —
see [../guides/websocket.md](../guides/websocket.md).

## ⚠️ Caveats

- **These are production endpoints** — Place/Modify/Cancel submit **real orders**.
  Use small quantities / far-from-market limit prices when testing.
- The **Quotes** request path/params are a best-effort reference; verify against
  the current `quotes()` implementation if it fails.
- Never commit real credentials. The secret-typed variables are left blank on
  purpose; fill them only in your local Postman.
