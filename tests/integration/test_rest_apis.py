import time
import traceback

from neo_api_client import NeoAPI


class APITestRunner:
    def __init__(self):
        self.results = []

        self.client = NeoAPI(
            environment="prod",
            access_token=None,
            neo_fin_key=None,
            consumer_key="bea95af0-6d9c-4d0e-95ef-f05993b4f77f",
        )

    def validate_response(self, response, api_name):
        if response is None:
            raise RuntimeError(f"{api_name} returned None")

        if isinstance(response, dict):
            if "error" in response:
                raise RuntimeError(f"{api_name} failed: {response}")

            if "Error" in response:
                raise RuntimeError(f"{api_name} failed: {response}")

        return response

    def run_test(self, api_name, func):
        print(f"\n{'=' * 80}")
        print(f"TESTING: {api_name}")
        print(f"{'=' * 80}")

        start = time.perf_counter()

        try:
            response = func()

            latency_ms = round((time.perf_counter() - start) * 1000, 2)

            self.validate_response(response, api_name)

            print(f"✅ PASS ({latency_ms} ms)")

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

runner.run_test(
    "TOTP LOGIN",
    lambda: runner.client.totp_login(
        mobile_number="+91XXXXXXXXXX",  # Replace with your mobile number
        ucc="YOUR_UCC",  # Replace with your UCC
        totp="817859",  # Replace with current TOTP
    ),
)

runner.run_test(
    "TOTP VALIDATE",
    lambda: runner.client.totp_validate(mpin="YOUR_MPIN"),  # Replace with your MPIN
)

print("\nConfiguration")
print("base_url:", runner.client.api_client.configuration.base_url)
print("sid:", runner.client.api_client.configuration.sid)

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
)

# ---------------------------
# LOGOUT
# ---------------------------

runner.run_test(
    "LOGOUT",
    lambda: runner.client.logout(),
)

runner.print_summary()
