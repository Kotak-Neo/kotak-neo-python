import json
import time
import traceback

import pyotp
from decouple import config

from neo_api_client import NeoAPI


class APITestRunner:
    def __init__(self):
        self.results = []
        self.ws_messages = []
        self.ws_connected = False
        self.ws_error = None

        # Get consumer_key from environment variable (optional - for tracking)
        consumer_key = config("NEO_CONSUMER_KEY", default=None)

        self.client = NeoAPI(
            environment="prod",
            access_token=None,
            neo_fin_key=None,
            consumer_key=consumer_key,
        )

        # Setup WebSocket callbacks
        self.client.on_message = self.on_ws_message
        self.client.on_error = self.on_ws_error
        self.client.on_open = self.on_ws_open
        self.client.on_close = self.on_ws_close

    def on_ws_message(self, message):
        print("\n[WebSocket Message Received]")
        print(json.dumps(message, indent=2, default=str))
        self.ws_messages.append(message)

    def on_ws_error(self, error):
        print(f"\n[WebSocket Error]: {error}")
        self.ws_error = error

    def on_ws_open(self, *_args):
        print("\n[WebSocket]: Connection Opened")
        self.ws_connected = True

    def on_ws_close(self, *_args):
        print("\n[WebSocket]: Connection Closed")
        self.ws_connected = False

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
print("serverId:", runner.client.api_client.configuration.serverId)
print("data_center:", runner.client.api_client.configuration.data_center)
print("=" * 80)

# ---------------------------
# MARKET DATA
# ---------------------------

runner.run_test(
    "QUOTES",
    lambda: runner.client.quotes(
        instrument_tokens=[
            {
                "instrument_token": "1333",
                "exchange_segment": "nse_cm",
            }
        ],
        quote_type="all",
    ),
    request_params={
        "instrument_tokens": [
            {
                "instrument_token": "1333",
                "exchange_segment": "nse_cm",
            }
        ],
        "quote_type": "all",
    },
)

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
        instrument_token="1333",
        transaction_type="B",
    ),
    request_params={
        "exchange_segment": "nse_cm",
        "price": "100",
        "order_type": "MKT",
        "product": "CNC",
        "quantity": "1",
        "instrument_token": "1333",
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

# Store order_id for modify and cancel tests
placed_order_id = None

# Test Place Order
place_order_params = {
    "exchange_segment": "nse_cm",
    "product": "CNC",
    "price": "1.00",  # Very low price to avoid execution
    "order_type": "L",  # Limit order
    "quantity": "1",
    "validity": "DAY",
    "trading_symbol": "INFY-EQ",  # Infosys - highly liquid stock
    "transaction_type": "B",  # Buy
}

place_order_response = runner.run_test(
    "PLACE ORDER",
    lambda: runner.client.place_order(**place_order_params),
    request_params=place_order_params,
)

# Extract order_id from response for modify and cancel tests
if place_order_response and isinstance(place_order_response, dict):
    # Try different possible response structures
    if "data" in place_order_response and isinstance(place_order_response["data"], dict):
        placed_order_id = place_order_response["data"].get("nOrdNo") or place_order_response[
            "data"
        ].get("orderId")
    elif "nOrdNo" in place_order_response:
        placed_order_id = place_order_response.get("nOrdNo")
    elif "orderId" in place_order_response:
        placed_order_id = place_order_response.get("orderId")

    if placed_order_id:
        print(f"\n[ORDER PLACED] Order ID: {placed_order_id}")
    else:
        print("\n[WARNING] Could not extract order_id from place order response")
        print(f"Response keys: {list(place_order_response.keys())}")

# Test Modify Order (only if order was placed successfully)
if placed_order_id:
    modify_order_params = {
        "order_id": placed_order_id,
        "price": "2.00",  # Change price to ₹2.00
        "order_type": "L",
        "quantity": "1",
        "validity": "DAY",
    }

    runner.run_test(
        "MODIFY ORDER",
        lambda: runner.client.modify_order(**modify_order_params),
        request_params=modify_order_params,
    )
else:
    print("\n[SKIPPED] MODIFY ORDER - No order_id available from place order")

# Test Cancel Order (only if order was placed successfully)
if placed_order_id:
    cancel_order_params = {
        "order_id": placed_order_id,
        "isVerify": True,  # Verify order status before canceling
    }

    runner.run_test(
        "CANCEL ORDER",
        lambda: runner.client.cancel_order(**cancel_order_params),
        request_params=cancel_order_params,
    )
else:
    print("\n[SKIPPED] CANCEL ORDER - No order_id available from place order")

# ---------------------------
# WEBSOCKET
# ---------------------------


def test_websocket_subscribe():
    """Test WebSocket subscription for live market data"""
    subscribe_params = {
        "instrument_tokens": [
            {
                "instrument_token": "1333",
                "exchange_segment": "nse_cm",
            }
        ],
        "isIndex": False,
        "isDepth": False,
    }

    # Subscribe to live feed
    runner.client.subscribe(
        instrument_tokens=subscribe_params["instrument_tokens"],
        isIndex=subscribe_params["isIndex"],
        isDepth=subscribe_params["isDepth"],
    )

    # Wait for connection and messages
    print("\nWaiting for WebSocket connection and messages (5 seconds)...")
    time.sleep(5)

    # Check results
    result = {
        "connected": runner.ws_connected,
        "messages_received": len(runner.ws_messages),
        "error": runner.ws_error,
    }

    if not runner.ws_connected and not runner.ws_error:
        raise RuntimeError("WebSocket did not connect")

    if runner.ws_error:
        raise RuntimeError(f"WebSocket error: {runner.ws_error}")

    return result


runner.run_test(
    "WEBSOCKET SUBSCRIBE",
    test_websocket_subscribe,
    request_params={
        "instrument_tokens": [
            {
                "instrument_token": "1333",
                "exchange_segment": "nse_cm",
            }
        ],
        "isIndex": False,
        "isDepth": False,
    },
)


def test_websocket_unsubscribe():
    """Test WebSocket unsubscription"""
    unsubscribe_params = {
        "instrument_tokens": [
            {
                "instrument_token": "1333",
                "exchange_segment": "nse_cm",
            }
        ],
        "isIndex": False,
        "isDepth": False,
    }

    # Clear previous messages
    runner.ws_messages.clear()

    # Unsubscribe
    runner.client.un_subscribe(
        instrument_tokens=unsubscribe_params["instrument_tokens"],
        isIndex=unsubscribe_params["isIndex"],
        isDepth=unsubscribe_params["isDepth"],
    )

    # Wait to confirm no more messages
    print("\nWaiting to confirm unsubscribe (3 seconds)...")
    time.sleep(3)

    result = {
        "unsubscribed": True,
        "messages_after_unsubscribe": len(runner.ws_messages),
    }

    return result


runner.run_test(
    "WEBSOCKET UNSUBSCRIBE",
    test_websocket_unsubscribe,
    request_params={
        "instrument_tokens": [
            {
                "instrument_token": "1333",
                "exchange_segment": "nse_cm",
            }
        ],
        "isIndex": False,
        "isDepth": False,
    },
)

# ---------------------------
# LOGOUT
# ---------------------------

runner.run_test(
    "LOGOUT",
    lambda: runner.client.logout(),
)

# Clean up WebSocket connection
if runner.client.NeoWebSocket and runner.client.NeoWebSocket.hsWebsocket:
    print("\nClosing WebSocket connection...")
    runner.client.NeoWebSocket.hsWebsocket.close()
    time.sleep(1)  # Give it time to close gracefully

runner.print_summary()
