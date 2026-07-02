import asyncio
import json
import time
import traceback

import pyotp
from decouple import config

from neo_api_client import NeoAPI
from neo_api_client.websocket.feed import WsToken


class APITestRunner:
    def __init__(self):
        self.results = []
        self.ws_messages = []
        self.ws_connected = False
        self.ws_error = None

        # Get consumer_key from environment variable (optional - for tracking)
        consumer_key = config("NEO_CONSUMER_KEY", default=None)

        # Use UAT environment for tests (configurable via NEO_ENVIRONMENT)
        environment = config("NEO_ENVIRONMENT", default="uat")

        self.client = NeoAPI(
            consumer_key=consumer_key,
            environment=environment,
            access_token=None,
            neo_fin_key=None,
        )

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

            self.results.append(
                {
                    "api": api_name,
                    "status": "PASS",
                    "latency_ms": latency_ms,
                }
            )

            return response

        except Exception as e:
            latency_ms = round((time.perf_counter() - start) * 1000, 2)

            print(f"❌ FAIL ({latency_ms} ms)")
            print(str(e))

            self.results.append(
                {
                    "api": api_name,
                    "status": "FAIL",
                    "latency_ms": latency_ms,
                    "error": str(e),
                }
            )

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

# Generate TOTP automatically if secret is provided
if TOTP_SECRET:
    totp_generator = pyotp.TOTP(TOTP_SECRET)
    totp_code = totp_generator.now()
    print(f"\n[AUTO-GENERATED TOTP]: {totp_code}")
else:
    # Fallback to manual TOTP if secret not provided
    totp_code = input("Enter TOTP code: ")
    print(f"\n[MANUAL TOTP]: {totp_code}")

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

runner.run_test(
    "ORDER REPORT",
    lambda: runner.client.order_report(),
)

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
    lambda: runner.client.limits(
        segment="ALL",
        exchange="ALL",
        product="ALL",
    ),
    request_params={
        "segment": "ALL",
        "exchange": "ALL",
        "product": "ALL",
    },
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

runner.run_test(
    "SEARCH SCRIP",
    lambda: runner.client.search_scrip(
        exchange_segment="nse_cm",
        symbol="RELIANCE",
    ),
    request_params={
        "exchange_segment": "nse_cm",
        "symbol": "RELIANCE",
    },
)

# ---------------------------
# ORDER MANAGEMENT (Place → Modify → Cancel)
# ---------------------------
# NOTE: Temporarily disabled. Re-enable to test the order lifecycle.
#
# # Store order_id for modify and cancel tests
# placed_order_id = None
#
# # Calculate order price based on LTP
# if ltp and ltp > 1:
#     order_price = f"{ltp - 1:.2f}"  # LTP - 1 to avoid execution
#     modify_price = f"{ltp - 2:.2f}"  # LTP - 2 for modify order
#     print(f"\n[ORDER PRICE] Using LTP-based pricing: Order=₹{order_price}, Modify=₹{modify_price}")
# else:
#     # Fallback to hardcoded price if LTP not available
#     order_price = "28.00"
#     modify_price = "27.00"
#     print(f"\n[ORDER PRICE] Using fallback pricing: Order=₹{order_price}, Modify=₹{modify_price}")
#
# # Test Place Order
# place_order_params = {
#     "exchange_segment": "nse_cm",
#     "product": "CNC",
#     "price": order_price,  # LTP - 1 to avoid execution
#     "order_type": "L",  # Limit order
#     "quantity": "1",
#     "validity": "DAY",
#     "trading_symbol": trading_symbol,
#     "transaction_type": "B",  # Buy
# }
#
# place_order_response = runner.run_test(
#     "PLACE ORDER",
#     lambda: runner.client.place_order(**place_order_params),
#     request_params=place_order_params,
# )
#
# # Extract order_id from response for modify and cancel tests
# if place_order_response and isinstance(place_order_response, dict):
#     # Try different possible response structures
#     if "data" in place_order_response and isinstance(place_order_response["data"], dict):
#         placed_order_id = place_order_response["data"].get("nOrdNo") or place_order_response[
#             "data"
#         ].get("orderId")
#     elif "nOrdNo" in place_order_response:
#         placed_order_id = place_order_response.get("nOrdNo")
#     elif "orderId" in place_order_response:
#         placed_order_id = place_order_response.get("orderId")
#
#     if placed_order_id:
#         print(f"\n[ORDER PLACED] Order ID: {placed_order_id}")
#     else:
#         print("\n[WARNING] Could not extract order_id from place order response")
#         print(f"Response keys: {list(place_order_response.keys())}")
#
# # Test Modify Order (only if order was placed successfully)
# if placed_order_id:
#     modify_order_params = {
#         "order_id": placed_order_id,
#         "price": modify_price,  # LTP - 2 to avoid execution
#         "order_type": "L",
#         "quantity": "1",
#         "validity": "DAY",
#     }
#
#     runner.run_test(
#         "MODIFY ORDER",
#         lambda: runner.client.modify_order(**modify_order_params),
#         request_params=modify_order_params,
#     )
# else:
#     print("\n[SKIPPED] MODIFY ORDER - No order_id available from place order")
#
# # Test Cancel Order (only if order was placed successfully)
# if placed_order_id:
#     cancel_order_params = {
#         "order_id": placed_order_id,
#         "isVerify": True,  # Verify order status before canceling
#     }
#
#     runner.run_test(
#         "CANCEL ORDER",
#         lambda: runner.client.cancel_order(**cancel_order_params),
#         request_params=cancel_order_params,
#     )
# else:
#     print("\n[SKIPPED] CANCEL ORDER - No order_id available from place order")

# ---------------------------
# WEBSOCKET (SFeed async client)
# ---------------------------


# Tokens for the documented WebSocket operations
LTP_TOKENS = [WsToken("nse_cm", "Nifty 50")]  # LTP by index name

# Option chain: a batch of NSE F&O tokens (subset of the documented list)
OPTION_CHAIN_TOKENS = [
    WsToken("nse_fo", str(t))
    for t in (
        44498,
        44500,
        44510,
        44512,
        44514,
        44516,
        44518,
        44520,
        44499,
        44501,
        44511,
        44513,
        44515,
        44517,
        44519,
        44521,
    )
]


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

            await ws.connect()
            runner.ws_connected = ws.is_connected

            await ws.subscribe_scrips(tokens)
            print(f"\nSubscribed to {len(tokens)} token(s) - receiving (5 seconds)...")
            try:
                async with asyncio.timeout(5):
                    async for message in ws:
                        runner.on_ws_message(message)
            except TimeoutError:
                pass  # Expected - we only listen for a fixed window

            await ws.close()

        asyncio.run(_run())

        if runner.ws_error:
            raise RuntimeError(f"WebSocket error: {runner.ws_error}")

        return {
            "subscribed_tokens": len(tokens),
            "messages_received": len(runner.ws_messages),
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

            await ws.connect()

            # Subscribe briefly so we know the feed is live.
            await ws.subscribe_scrips(tokens)
            print(f"\nSubscribed to {len(tokens)} token(s) - receiving briefly (3 seconds)...")
            try:
                async with asyncio.timeout(3):
                    async for _message in ws:
                        pass
            except TimeoutError:
                pass

            # Unsubscribe, then count any messages that still arrive.
            await ws.unsubscribe_scrips(tokens)
            print("\nUnsubscribed - confirming feed goes quiet (3 seconds)...")
            messages_after = 0
            try:
                async with asyncio.timeout(3):
                    async for _message in ws:
                        messages_after += 1
            except TimeoutError:
                pass

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
    request_params={"inputtoken": [t.inputtoken for t in LTP_TOKENS]},
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
    request_params={"inputtoken": [t.inputtoken for t in OPTION_CHAIN_TOKENS]},
)

runner.run_test(
    "WEBSOCKET OPTION CHAIN UNSUBSCRIBE",
    _ws_unsubscribe_test(OPTION_CHAIN_TOKENS),
    request_params={"inputtoken": [t.inputtoken for t in OPTION_CHAIN_TOKENS]},
)

# ---------------------------
# LOGOUT
# ---------------------------

runner.run_test(
    "LOGOUT",
    lambda: runner.client.logout(),
)

runner.print_summary()
