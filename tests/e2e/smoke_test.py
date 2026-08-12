import asyncio
import json
import time
import traceback
from datetime import date

import pyotp
from decouple import config

from neo_api_client import NeoAPI
from neo_api_client.utils import scrip_cache
from neo_api_client.websocket.feed import WsToken

# Header keys that carry secrets; masked when printed so credentials aren't
# leaked to the console/CI logs.
_SENSITIVE_HEADERS = {"authorization", "auth", "sid", "neo-fin-key", "x-access-token"}


def _mask_header(name, value):
    """Mask sensitive header values for safe printing."""
    if value is None:
        return None
    if name.lower() in _SENSITIVE_HEADERS and isinstance(value, str) and len(value) > 8:
        return value[:6] + "…" + value[-2:]
    return value


def _print_request_headers(request):
    """httpx request event hook: print the headers actually sent on each request.

    Registered on the SDK's shared httpx.Client so every REST call (login,
    orders, market data, ...) shows its outgoing headers — useful for confirming
    that headers like X-Forwarded-For are attached in the UAT environment.
    """
    print(f"\n[HTTP →] {request.method} {request.url}")
    print("[HTTP → headers]")
    for key, value in request.headers.items():
        print(f"    {key}: {_mask_header(key, value)}")


async def _collect_for(ws, seconds, on_message=None):
    """Read messages from `ws` for a fixed window, then stop.

    Uses ``asyncio.wait_for`` so it works on Python 3.10 (where
    ``asyncio.timeout`` is unavailable). Returns the number of messages seen.
    """
    count = 0
    loop = asyncio.get_event_loop()
    deadline = loop.time() + seconds
    while True:
        remaining = deadline - loop.time()
        if remaining <= 0:
            break
        try:
            message = await asyncio.wait_for(ws.__anext__(), timeout=remaining)
        except (asyncio.TimeoutError, StopAsyncIteration):
            break
        count += 1
        if on_message:
            on_message(message)
    return count


class APITestRunner:
    def __init__(self):
        self.results = []
        self.ws_messages = []
        self.ws_connected = False
        self.ws_error = None

        # Get consumer_key from environment variable (optional - for tracking)
        consumer_key = config("NEO_CONSUMER_KEY", default=None)

        # SDK developers only: NEO_ENVIRONMENT selects the backend for test runs
        # (defaults to the internal UAT environment). Not used by normal SDK
        # consumers, who always run against production.
        environment = config("NEO_ENVIRONMENT", default="uat")

        self.client = NeoAPI(
            consumer_key=consumer_key,
            environment=environment,
            access_token=None,
            neo_fin_key=None,
        )

        # Show the actual outgoing headers for every REST request by hooking the
        # SDK's shared httpx.Client. This confirms which headers (e.g.
        # X-Forwarded-For in UAT) are attached on the wire.
        session = self.client.api_client.rest_client.session
        session.event_hooks["request"].append(_print_request_headers)

        # Report the environment + whether the UAT X-Forwarded-For is configured.
        cfg = self.client.api_client.configuration
        print("\n" + "=" * 80)
        print("REQUEST HEADER CONFIGURATION")
        print("=" * 80)
        print("environment:", cfg.host)
        xff = getattr(cfg, "uat_x_forwarded_for", None)
        if cfg.host == "uat":
            print("X-Forwarded-For (UAT):", xff if xff else "NOT SET (NEO_UAT_X_FORWARDED_FOR)")
        else:
            print("X-Forwarded-For: not applicable (only sent in UAT)")
        print("=" * 80)

    def on_ws_message(self, message):
        print("\n[WebSocket Message Received]")
        print(json.dumps(message.model_dump(), indent=2, default=str))
        self.ws_messages.append(message)

    def on_ws_error(self, error):
        print(f"\n[WebSocket Error]: {error}")
        self.ws_error = error

    def validate_response(self, response, api_name):
        if response is None:
            raise RuntimeError(f"{api_name} returned None")

        if isinstance(response, dict):
            # Check if error value is truthy (not None, not empty)
            if response.get("error"):
                raise RuntimeError(f"{api_name} failed: {response}")

            if response.get("Error"):
                raise RuntimeError(f"{api_name} failed: {response}")

            # Check for stat != "Ok" (API error format)
            if response.get("stat") == "Not_Ok":
                error_code = response.get("stCode", "Unknown code")
                error_msg = response.get("errMsg", "Unknown error")

                # 5203 = "No Data" - This is a valid response, not an error
                # It just means there are no orders/trades/positions
                if error_code == 5203:
                    print(f"\n[INFO] {api_name}: {error_msg} - This is normal when there's no data")
                    return response

                # Other error codes are actual errors
                raise RuntimeError(f"{api_name} failed: {error_msg} (Code: {error_code})")

        return response

    def run_test(self, api_name, func, request_params=None):
        print(f"\n{'=' * 80}")
        print(f"TESTING: {api_name}")
        print(f"{'=' * 80}")

        # Print request parameters if provided
        if request_params:
            print("\nREQUEST:")
            print(json.dumps(request_params, indent=2, default=str))

        start = time.perf_counter()

        try:
            response = func()

            latency_ms = round((time.perf_counter() - start) * 1000, 2)

            self.validate_response(response, api_name)

            print(f"✅ PASS ({latency_ms} ms)")

            # Print JSON response
            print("\nRESPONSE:")
            print(json.dumps(response, indent=2, default=str))

            self.results.append({
                "api": api_name,
                "status": "PASS",
                "latency_ms": latency_ms,
            })

            return response

        except Exception as e:
            latency_ms = round((time.perf_counter() - start) * 1000, 2)

            print(f"❌ FAIL ({latency_ms} ms)")
            print(str(e))

            self.results.append({
                "api": api_name,
                "status": "FAIL",
                "latency_ms": latency_ms,
                "error": str(e),
            })

            traceback.print_exc()

            return None

    def print_summary(self):
        print("\n")
        print("=" * 100)
        print("API PERFORMANCE SUMMARY")
        print("=" * 100)

        for result in self.results:
            print(f"{result['api']:<35}{result['status']:<10}{result['latency_ms']:>10} ms")


runner = APITestRunner()

# ---------------------------
# LOGIN
# ---------------------------

# Get credentials from .env file (required - no defaults)
try:
    MOBILE_NUMBER = config("NEO_MOBILE_NUMBER")
    UCC = config("NEO_UCC")
    TOTP_SECRET = config("NEO_TOTP_SECRET")
    MPIN = config("NEO_MPIN")
except Exception as e:
    print("\n" + "=" * 80)
    print("ERROR: Missing required environment variables in .env file")
    print("=" * 80)
    print(f"\n{e}")
    print("\nPlease ensure .env file exists with the following variables:")
    print("  - NEO_MOBILE_NUMBER")
    print("  - NEO_UCC")
    print("  - NEO_TOTP_SECRET")
    print("  - NEO_MPIN")
    print("\nSee .env.example for template")
    print("=" * 80)
    exit(1)

# Ask whether to auto-generate the TOTP from NEO_TOTP_SECRET (via pyotp) or
# enter it manually. Automatic is the default; answer "y" to type it in by
# hand instead (e.g. to test with a different authenticator/device).
enter_totp_manually = input(
    "\nEnter TOTP manually instead of auto-generating it? (y/N): "
).strip().lower() in ("y", "yes")

if enter_totp_manually:
    totp_code = input("Enter TOTP code: ").strip()
    print(f"\n[MANUAL TOTP]: {totp_code}")
else:
    totp_generator = pyotp.TOTP(TOTP_SECRET)
    totp_code = totp_generator.now()
    print(f"\n[AUTO-GENERATED TOTP]: {totp_code}")

totp_login_params = {
    "mobile_number": MOBILE_NUMBER,
    "ucc": UCC,
    "totp": totp_code,
}

runner.run_test(
    "TOTP LOGIN",
    lambda: runner.client.totp_login(**totp_login_params),
    request_params=totp_login_params,
)

runner.run_test(
    "TOTP VALIDATE",
    lambda: runner.client.totp_validate(mpin=MPIN),
    request_params={"mpin": MPIN},
)

print("\n" + "=" * 80)
print("AUTHENTICATION STATUS")
print("=" * 80)
print("base_url:", runner.client.api_client.configuration.base_url)
print("sid:", runner.client.api_client.configuration.sid)
print("edit_sid:", runner.client.api_client.configuration.edit_sid)
print(
    "edit_token:",
    runner.client.api_client.configuration.edit_token[:50] + "..."
    if runner.client.api_client.configuration.edit_token
    else None,
)
print("data_center:", runner.client.api_client.configuration.data_center)
print("=" * 80)

# ---------------------------
# WHAT'S MY IP
# ---------------------------

runner.run_test(
    "WHATS MY IP",
    lambda: runner.client.whatsmyip(),
)

# ---------------------------
# MARKET DATA
# ---------------------------

quotes_response = runner.run_test(
    "QUOTES",
    lambda: runner.client.quotes(
        instrument_tokens=[
            {
                "instrument_token": "19084",
                "exchange_segment": "nse_cm",
            }
        ],
        quote_type="all",
    ),
    request_params={
        "instrument_tokens": [
            {
                "instrument_token": "19084",
                "exchange_segment": "nse_cm",
            }
        ],
        "quote_type": "all",
    },
)

# Extract LTP from quotes response for use in place order
ltp = None
trading_symbol = "ITBEES-EQ"  # Default
if quotes_response and isinstance(quotes_response, dict):
    try:
        # Try to extract LTP from different possible response structures
        if "data" in quotes_response and isinstance(quotes_response["data"], list):
            if len(quotes_response["data"]) > 0:
                quote_data = quotes_response["data"][0]
                ltp = float(quote_data.get("ltp", 0))
                trading_symbol = quote_data.get("trdSym", trading_symbol)
        elif "ltp" in quotes_response:
            ltp = float(quotes_response["ltp"])

        if ltp and ltp > 0:
            print(f"\n[LTP CAPTURED] {trading_symbol}: ₹{ltp}")
        else:
            print("\n[WARNING] Could not extract valid LTP from quotes response")
            ltp = None
    except (ValueError, TypeError, KeyError) as e:
        print(f"\n[WARNING] Error extracting LTP: {e}")
        ltp = None

# ---------------------------
# REPORTS
# ---------------------------

order_report_response = runner.run_test(
    "ORDER REPORT",
    lambda: runner.client.order_report(),
)

# Capture an order number from the order book so we can exercise the
# order-book-by-order-id endpoint (/quick/user/orders/<order_no>).
first_order_no = None
if order_report_response and isinstance(order_report_response, dict):
    orders = order_report_response.get("data")
    if isinstance(orders, list) and orders:
        first_order_no = orders[0].get("nOrdNo")

if first_order_no:
    runner.run_test(
        "ORDER REPORT BY ID",
        lambda: runner.client.order_report(order_id=first_order_no),
        request_params={"order_id": first_order_no},
    )
else:
    print("\n[SKIPPED] ORDER REPORT BY ID - No order number available from order book")

if first_order_no:
    runner.run_test(
        "ORDER HISTORY",
        lambda: runner.client.order_history(order_id=first_order_no),
        request_params={"order_id": first_order_no},
    )
else:
    print("\n[SKIPPED] ORDER HISTORY - No order number available from order book")

runner.run_test(
    "TRADE REPORT",
    lambda: runner.client.trade_report(),
)

runner.run_test(
    "POSITIONS",
    lambda: runner.client.positions(),
)

runner.run_test(
    "HOLDINGS",
    lambda: runner.client.holdings(),
)

runner.run_test(
    "LIMITS",
    lambda: runner.client.limits(),
)

# ---------------------------
# MARGIN
# ---------------------------

runner.run_test(
    "MARGIN REQUIRED",
    lambda: runner.client.margin_required(
        exchange_segment="nse_cm",
        price="100",
        order_type="MKT",
        product="CNC",
        quantity="1",
        instrument_token="19084",
        transaction_type="B",
    ),
    request_params={
        "exchange_segment": "nse_cm",
        "price": "100",
        "order_type": "MKT",
        "product": "CNC",
        "quantity": "1",
        "instrument_token": "19084",
        "transaction_type": "B",
    },
)

# ---------------------------
# SCRIP MASTER
# ---------------------------

runner.run_test(
    "SCRIP MASTER",
    lambda: runner.client.scrip_master(),
)

runner.run_test(
    "SCRIP MASTER NSE_CM",
    lambda: runner.client.scrip_master(exchange_segment="nse_cm"),
    request_params={"exchange_segment": "nse_cm"},
)

# ---------------------------
# SEARCH SCRIP
# ---------------------------

# search_scrip() builds its own headers (Authorization + Content-Type) for the
# scrip_master lookup it makes internally, but the CSV file download that
# follows is a plain unauthenticated GET straight to the file's URL (no Kotak
# API headers) -- print both explicitly since search_scrip() itself doesn't
# use the SDK's shared httpx.Client, so the request-hook logging above never
# fires for it.
print("\n[SEARCH SCRIP REQUEST HEADERS]")
print("Step 1 - scrip_master lookup:")
print(
    f"    Authorization: {_mask_header('authorization', runner.client.api_client.configuration.consumer_key)}"
)
print("    Content-Type: application/x-www-form-urlencoded")
print("Step 2 - CSV file download: plain GET to the resolved file URL, no headers")

# search_scrip() caches the downloaded scrip-master CSV on disk for the rest
# of the calendar day (see neo_api_client.utils.scrip_cache); print the exact
# path it reads from / writes to for this exchange_segment, and whether it's
# already cached from an earlier run today. Cached under the canonical
# segment name ("bse_fo"), not the alias passed below ("bfo") -- the SDK
# resolves the alias before touching the cache.
_search_scrip_segment = "bse_fo"
_scrip_cache_path = scrip_cache._cache_path(_search_scrip_segment, date.today())
print(f"\n[SEARCH SCRIP CACHE FILE] {_scrip_cache_path}")
print(
    "cached:", "yes (reused, no download)" if _scrip_cache_path.exists() else "no (will download)"
)

search_scrip_response = runner.run_test(
    "SEARCH SCRIP",
    lambda: runner.client.search_scrip(
        exchange_segment="bfo",
        symbol="sensex",
        expiry="27AUG2026",
        ignore_50multiple=False,
    ),
    request_params={
        "exchange_segment": "bfo",
        "symbol": "sensex",
        "expiry": "27AUG2026",
        "ignore_50multiple": False,
    },
)

print("\n[SEARCH SCRIP OUTPUT]")
if isinstance(search_scrip_response, list):
    print(f"Matched {len(search_scrip_response)} scrip(s):")
print(json.dumps(search_scrip_response, indent=2, default=str))

# ---------------------------
# ORDER MANAGEMENT (Place → Modify → Cancel)
# ---------------------------
# These tests place a REAL order and then modify/cancel it. Two modes:
#
#   * MANUAL   — you type every value by hand (no LTP-based pricing).
#   * AUTOMATIC — the original logic: place at LTP-1 and modify at LTP-2 so the
#                 order rests below market and is unlikely to execute.
#
# Choose the mode at the prompt below.


def _ask(prompt, default=None):
    """Prompt for a value, returning `default` when the user just hits Enter."""
    suffix = f" [{default}]" if default is not None else ""
    value = input(f"{prompt}{suffix}: ").strip()
    return value or default


def _ask_yes_no(prompt, default=False):
    """Prompt for a yes/no answer."""
    hint = "Y/n" if default else "y/N"
    value = input(f"{prompt} ({hint}): ").strip().lower()
    if not value:
        return default
    return value in ("y", "yes")


def _ask_action(operation):
    """Prompt whether to run an order operation. Returns one of:

    * "run"  — (y) execute this operation
    * "no"   — (N, default) do not execute this operation, continue to the next
    * "skip" — (S) skip this and all remaining order operations
    """
    value = (
        input(f"\nExecute {operation}?  (y = yes,  N = no,  S = skip remaining)  [y/N/S]: ")
        .strip()
        .lower()
    )
    if value in ("y", "yes"):
        return "run"
    if value in ("s", "skip"):
        return "skip"
    return "no"


def _extract_order_id(place_response):
    """Pull the order number out of a place_order response (various shapes)."""
    if not (place_response and isinstance(place_response, dict)):
        return None
    if "data" in place_response and isinstance(place_response["data"], dict):
        return place_response["data"].get("nOrdNo") or place_response["data"].get("orderId")
    return place_response.get("nOrdNo") or place_response.get("orderId")


def _run_order_lifecycle(place_builder, modify_builder, cancel_builder):
    """Interactively place, then modify and cancel an order.

    Each step is gated by a (y/N/S) prompt: run it, decline it, or skip all
    remaining steps. The builder callables are only invoked (i.e. values are
    only collected) when a step is actually going to run. `order_id` is filled
    in from the placed order for the modify/cancel steps.
    """
    # ---- PLACE ----
    action = _ask_action("PLACE ORDER")
    if action == "skip":
        print("\n[SKIPPED] ORDER MANAGEMENT - skipped remaining operations")
        return
    if action != "run":
        print("\n[SKIPPED] PLACE ORDER - declined; nothing to modify or cancel")
        return

    place_params = place_builder()
    place_response = runner.run_test(
        "PLACE ORDER",
        lambda: runner.client.place_order(**place_params),
        request_params=place_params,
    )

    order_id = _extract_order_id(place_response)
    if order_id:
        print(f"\n[ORDER PLACED] Order ID: {order_id}")
    else:
        print("\n[WARNING] Could not extract order_id from place order response")
        if isinstance(place_response, dict):
            print(f"Response keys: {list(place_response.keys())}")
        print("[SKIPPED] MODIFY / CANCEL - No order_id available from place order")
        return

    # ---- MODIFY ----
    action = _ask_action("MODIFY ORDER")
    if action == "skip":
        print("\n[SKIPPED] MODIFY / CANCEL - skipped remaining operations")
        return
    if action == "run":
        modify_params = {**modify_builder(), "order_id": order_id}
        runner.run_test(
            "MODIFY ORDER",
            lambda: runner.client.modify_order(**modify_params),
            request_params=modify_params,
        )
    else:
        print("\n[SKIPPED] MODIFY ORDER - declined")

    # ---- CANCEL ----
    action = _ask_action("CANCEL ORDER")
    if action == "run":
        cancel_params = {**cancel_builder(), "order_id": order_id}
        runner.run_test(
            "CANCEL ORDER",
            lambda: runner.client.cancel_order(**cancel_params),
            request_params=cancel_params,
        )
    else:
        # For the final step, "no" and "skip" are equivalent.
        print("\n[SKIPPED] CANCEL ORDER - declined")


print("\n" + "=" * 80)
print("ORDER MANAGEMENT (Place → Modify → Cancel)")
print("=" * 80)
print(
    "This will place a REAL order, then modify and cancel it.\n"
    "\nFirst choose how order values are supplied:\n"
    "  y -> enter every value manually.\n"
    "  N -> automatic: place at LTP-1, modify at LTP-2 (original logic).\n"
    "  S -> skip all remaining order operations."
)

_order_mode = input("\nEnter order values manually? (y/N/S): ").strip().lower()

if _order_mode in ("s", "skip"):
    print("\n[SKIPPED] ORDER MANAGEMENT - skipped all order operations")
elif _order_mode in ("y", "yes"):
    # ---- MANUAL: every value typed in (collected only when a step runs) ----
    def _place_builder():
        return {
            "exchange_segment": _ask("Exchange segment", default="nse_cm"),
            "product": _ask("Product (CNC/MIS/NRML)", default="CNC"),
            "price": _ask("Order price", default="1.00"),
            "order_type": _ask("Order type (L/MKT/SL/SL-M)", default="L"),
            "quantity": _ask("Quantity", default="1"),
            "validity": _ask("Validity (DAY/IOC)", default="DAY"),
            "trading_symbol": _ask("Trading symbol", default="ITBEES-EQ"),
            "transaction_type": _ask("Transaction type (B/S)", default="B"),
        }

    def _modify_builder():
        return {
            "price": _ask("New order price", default="1.00"),
            "order_type": _ask("Order type (L/MKT/SL/SL-M)", default="L"),
            "quantity": _ask("Quantity", default="1"),
            "validity": _ask("Validity (DAY/IOC)", default="DAY"),
        }

    def _cancel_builder():
        return {"isVerify": _ask_yes_no("Verify order status before cancelling?", default=True)}

    _run_order_lifecycle(_place_builder, _modify_builder, _cancel_builder)

else:
    # ---- AUTOMATIC: LTP-based pricing (original logic) ----
    # Order rests below market (LTP-1) so it is unlikely to execute; modify to
    # LTP-2 to keep it resting.
    if ltp and ltp > 1:
        order_price = f"{ltp - 1:.2f}"
        modify_price = f"{ltp - 2:.2f}"
        print(f"\n[ORDER PRICE] LTP-based pricing: Order=₹{order_price}, Modify=₹{modify_price}")
    else:
        order_price = "28.00"
        modify_price = "27.00"
        print(f"\n[ORDER PRICE] Fallback pricing: Order=₹{order_price}, Modify=₹{modify_price}")

    _run_order_lifecycle(
        lambda: {
            "exchange_segment": "nse_cm",
            "product": "CNC",
            "price": order_price,  # LTP - 1 to avoid execution
            "order_type": "L",  # Limit order
            "quantity": "1",
            "validity": "DAY",
            "trading_symbol": trading_symbol,
            "transaction_type": "B",  # Buy
        },
        lambda: {
            "price": modify_price,  # LTP - 2 to avoid execution
            "order_type": "L",
            "quantity": "1",
            "validity": "DAY",
        },
        lambda: {"isVerify": True},
    )

# ---------------------------
# WEBSOCKET (SFeed async client)
# ---------------------------


# Tokens for the documented WebSocket operations
LTP_TOKENS = [WsToken("nse_cm", "Nifty 50")]  # LTP by index name

# Option chain: underlying + a batch of NSE F&O contract tokens
OPTION_CHAIN_TOKENS = [
    WsToken(*pair.split("|"))
    for pair in (
        "nse_cm|2885",
        "nse_cm|22",
        "nse_fo|61593",
        "nse_fo|58073",
        "nse_fo|58072",
        "nse_fo|58067",
        "nse_fo|58070",
        "nse_fo|58071",
        "nse_fo|61153",
        "nse_fo|61148",
        "nse_fo|61155",
        "nse_fo|61172",
        "nse_fo|61174",
    )
]


def _trace_ws_frames(ws):
    """Wrap the live socket's send() so every outgoing WS frame is printed.

    The ``REQUEST`` block that run_test() prints is a display-only summary; this
    shows the ACTUAL frame put on the wire (including ``ack_symbol``).
    """
    original_send = ws._ws.send

    async def send_and_print(data):
        print(f"[WS →] {data}")
        return await original_send(data)

    ws._ws.send = send_and_print


def _ws_subscribe_test(tokens):
    """Connect, subscribe to `tokens`, collect messages for a few seconds.

    Returns a callable suitable for runner.run_test().
    """

    def _test():
        async def _run():
            runner.ws_messages.clear()
            runner.ws_error = None

            ws = runner.client.create_websocket()
            ws.on_message = runner.on_ws_message
            ws.on_error = runner.on_ws_error
            print(f"\n[WEBSOCKET URL] SFeed: {ws.url}")

            await ws.connect()
            runner.ws_connected = ws.is_connected
            _trace_ws_frames(ws)

            await ws.subscribe_scrips(tokens)
            print(f"\nSubscribed to {len(tokens)} token(s)")
            print("[TRADING SYMBOLS MAP] (from subscribe ack):")
            print(json.dumps(ws.trading_symbols, indent=2))

            print("\nReceiving (5 seconds)...")
            await _collect_for(ws, 5, on_message=runner.on_ws_message)

            await ws.close()

            return dict(ws.trading_symbols)

        trading_symbols = asyncio.run(_run())

        if runner.ws_error:
            raise RuntimeError(f"WebSocket error: {runner.ws_error}")

        return {
            "subscribed_tokens": len(tokens),
            "messages_received": len(runner.ws_messages),
            "trading_symbols": trading_symbols,
        }

    return _test


def _ws_unsubscribe_test(tokens):
    """Subscribe to `tokens`, unsubscribe, then confirm the feed goes quiet.

    Returns a callable suitable for runner.run_test().
    """

    def _test():
        async def _run():
            runner.ws_error = None

            ws = runner.client.create_websocket()
            ws.on_error = runner.on_ws_error
            print(f"\n[WEBSOCKET URL] SFeed: {ws.url}")

            await ws.connect()
            _trace_ws_frames(ws)

            # Subscribe briefly so we know the feed is live.
            await ws.subscribe_scrips(tokens)
            print(f"\nSubscribed to {len(tokens)} token(s) - receiving briefly (3 seconds)...")
            await _collect_for(ws, 3)

            # Unsubscribe, then count any messages that still arrive.
            await ws.unsubscribe_scrips(tokens)
            print("\nUnsubscribed - confirming feed goes quiet (3 seconds)...")
            messages_after = await _collect_for(ws, 3)

            await ws.close()
            return messages_after

        messages_after = asyncio.run(_run())

        if runner.ws_error:
            raise RuntimeError(f"WebSocket error: {runner.ws_error}")

        print(f"\n[UNSUBSCRIBE] Messages received after unsubscribe: {messages_after}")
        return {
            "unsubscribed": True,
            "unsubscribed_tokens": len(tokens),
            "messages_after_unsubscribe": messages_after,
        }

    return _test


# LTP subscribe / unsubscribe (single index token)
runner.run_test(
    "WEBSOCKET LTP SUBSCRIBE",
    _ws_subscribe_test(LTP_TOKENS),
    request_params={
        "inputtoken": [t.inputtoken for t in LTP_TOKENS],
        "ack_symbol": True,
    },
)

runner.run_test(
    "WEBSOCKET LTP UNSUBSCRIBE",
    _ws_unsubscribe_test(LTP_TOKENS),
    request_params={"inputtoken": [t.inputtoken for t in LTP_TOKENS]},
)

# Option chain subscribe / unsubscribe (batched NSE F&O tokens)
runner.run_test(
    "WEBSOCKET OPTION CHAIN SUBSCRIBE",
    _ws_subscribe_test(OPTION_CHAIN_TOKENS),
    request_params={
        "inputtoken": [t.inputtoken for t in OPTION_CHAIN_TOKENS],
        "ack_symbol": True,
    },
)

runner.run_test(
    "WEBSOCKET OPTION CHAIN UNSUBSCRIBE",
    _ws_unsubscribe_test(OPTION_CHAIN_TOKENS),
    request_params={"inputtoken": [t.inputtoken for t in OPTION_CHAIN_TOKENS]},
)

# ---------------------------
# ORDER & POSITION FEED (async client)
# ---------------------------


def _order_feed_test():
    """Connect to the order/position feed and collect messages for a window.

    The feed is fire-and-hose (no subscribe step): it streams whatever the
    account produces. With no live order/position activity this may see zero
    messages — a clean connect + graceful close is still a PASS.
    """

    def _test():
        async def _run():
            order_messages = []

            feed = runner.client.create_order_feed()
            feed.on_error = runner.on_ws_error
            print(f"\n[WEBSOCKET URL] Order feed: {feed.url}")

            await feed.connect()
            connected = feed.is_connected
            print(f"\nOrder feed connected: {connected} ({feed.url})")

            print("Listening for order/position updates (5 seconds)...")
            await _collect_for(feed, 5, on_message=order_messages.append)

            await feed.close()
            return connected, order_messages

        connected, order_messages = asyncio.run(_run())

        if runner.ws_error:
            raise RuntimeError(f"Order feed error: {runner.ws_error}")
        if not connected:
            raise RuntimeError("Order feed did not connect")

        for message in order_messages:
            # Most frames parse into a typed OrderUpdate/PositionUpdate, but
            # _parse_message() falls back to the raw dict/string for an
            # unrecognized type or a payload that doesn't fit the model.
            if hasattr(message, "model_dump"):
                print(json.dumps(message.model_dump(), indent=2, default=str))
            else:
                print(json.dumps(message, indent=2, default=str))

        return {
            "connected": connected,
            "messages_received": len(order_messages),
        }

    return _test


runner.ws_error = None
runner.run_test(
    "ORDER & POSITION FEED",
    _order_feed_test(),
)

# ---------------------------
# LOGOUT
# ---------------------------

runner.run_test(
    "LOGOUT",
    lambda: runner.client.logout(),
)

runner.print_summary()
