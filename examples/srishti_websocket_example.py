"""Example: Using Srishti WebSocket with async/await."""

import asyncio

from neo_api_client import NeoAPI
from neo_api_client.websocket.srishti import SFeedScrip, WsToken


async def main():
    """Main async function demonstrating Srishti WebSocket usage."""

    # Initialize NeoAPI client
    client = NeoAPI(
        consumer_key="your-consumer-key-here",
        environment="prod",  # or "uat" for testing
    )

    # Step 1: Login with TOTP
    print("Logging in...")
    login_response = client.totp_login(
        mobile_number="+919876543210",
        ucc="ABC123",
        totp="123456",  # Generate from authenticator app
    )
    print(f"Login response: {login_response.get('stat')}")

    # Step 2: Validate with MPIN
    print("Validating with MPIN...")
    validate_response = client.totp_validate(mpin="123456")
    print(f"Validate response: {validate_response.get('stat')}")

    # Step 3: Create WebSocket connection
    print("\nConnecting to Srishti WebSocket...")
    async with client.create_websocket() as ws:
        print("✓ Connected!")

        # Subscribe to scrips
        tokens = [
            WsToken("nse_cm", "1333"),  # RELIANCE
            WsToken("nse_cm", "11536"),  # TCS
            WsToken("nse_cm", "2885"),  # INFY
        ]

        print(f"\nSubscribing to {len(tokens)} scrips...")
        await ws.subscribe_scrips(tokens)
        print("✓ Subscribed!")

        # Process messages
        print("\nReceiving live market data (press Ctrl+C to stop)...\n")
        try:
            async for message in ws:
                # Type-safe message handling
                if isinstance(message, SFeedScrip):
                    print(
                        f"[{message.exchange_segment}:{message.instrument_token}] "
                        f"LTP: ₹{message.last_traded_price:.2f} | "
                        f"Change: {message.change:+.2f} ({message.percentage_change:+.2f}%) | "
                        f"Volume: {message.trade_volume:,}"
                    )

        except KeyboardInterrupt:
            print("\n\nStopping...")


async def example_with_callbacks():
    """Alternative: Using callbacks instead of async iteration."""

    client = NeoAPI(consumer_key="...", environment="prod")
    client.totp_login(mobile_number="+91...", ucc="...", totp="...")
    client.totp_validate(mpin="...")

    # Create WebSocket
    ws = client.create_websocket()

    # Set callbacks
    def on_message(msg):
        print(f"Received: {msg.last_traded_price}")

    def on_error(error):
        print(f"Error: {error}")

    ws.on_message = on_message
    ws.on_error = on_error

    # Connect and subscribe
    await ws.connect()
    await ws.subscribe_scrips([WsToken("nse_cm", "1333")])

    # Keep running
    try:
        await asyncio.Event().wait()
    finally:
        await ws.close()


async def example_multiple_subscriptions():
    """Example: Subscribe to scrips, index, and depth simultaneously."""

    client = NeoAPI(consumer_key="...", environment="prod")
    client.totp_login(mobile_number="+91...", ucc="...", totp="...")
    client.totp_validate(mpin="...")

    async with client.create_websocket() as ws:
        # Subscribe to different types
        await ws.subscribe_scrips([WsToken("nse_cm", "1333")])  # Scrip
        await ws.subscribe_index([WsToken("nse_cm", "26000")])  # NIFTY 50
        await ws.subscribe_depth([WsToken("nse_cm", "11536")])  # TCS depth

        # Process all types
        async for message in ws:
            match message.type:
                case "scrip":
                    print(f"Scrip LTP: {message.last_traded_price}")
                case "index":
                    print(f"Index: {message.last_traded_price}")
                case "depth":
                    print(f"Depth - Buy: {message.total_buy_qty}, Sell: {message.total_sell_qty}")


if __name__ == "__main__":
    # Run main example
    asyncio.run(main())

    # Or run alternative examples:
    # asyncio.run(example_with_callbacks())
    # asyncio.run(example_multiple_subscriptions())
