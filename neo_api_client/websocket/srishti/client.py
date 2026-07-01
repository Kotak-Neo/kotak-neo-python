"""Modern async/await WebSocket client for Srishti broadcast platform."""

import asyncio
import contextlib
import json
import ssl
from collections.abc import AsyncIterator, Callable
from typing import Any

import websockets
from pydantic import ValidationError
from websockets.client import WebSocketClientProtocol

from neo_api_client.websocket.srishti.exceptions import (
    AlreadyConnectedError,
    AuthenticationError,
    ConnectionError,
    MessageParseError,
    NotConnectedError,
    SubscriptionError,
)
from neo_api_client.websocket.srishti.models import (
    SFeedDepth,
    SFeedIndex,
    SFeedMessage,
    SFeedScrip,
    SFeedScripLite,
    WsToken,
)


class SrishtiWebSocket:
    """Modern async/await WebSocket client for Srishti broadcast platform.

    Features:
        - Async/await API with `async for` iteration
        - Type-safe Pydantic models
        - Automatic reconnection
        - Heartbeat management
        - Context manager support

    Example:
        ```python
        async with SrishtiWebSocket(access_token, sid) as client:
            await client.subscribe_scrips([
                WsToken("nse_cm", "1333"),
                WsToken("mcx_fo", "499095"),
            ])

            async for message in client:
                print(type(message).__name__, message.model_dump())
        ```

    Alternative without context manager:
        ```python
        client = SrishtiWebSocket(access_token, sid)
        await client.connect()

        await client.subscribe_scrips([WsToken("nse_cm", "1333")])

        async for message in client:
            print(message)

        await client.close()
        ```
    """

    def __init__(
        self,
        access_token: str,
        sid: str,
        url: str = "wss://mlhsm.kotaksecurities.com",  # TODO: Update with actual Srishti URL
        heartbeat_interval: int = 30,
        reconnect_delay: int = 5,
        max_reconnect_attempts: int = 5,
    ):
        """Initialize Srishti WebSocket client.

        Args:
            access_token: Authentication token
            sid: Session ID
            url: WebSocket URL (default: Srishti production URL)
            heartbeat_interval: Seconds between heartbeat pings (default: 30)
            reconnect_delay: Seconds to wait before reconnecting (default: 5)
            max_reconnect_attempts: Maximum reconnection attempts (default: 5)
        """
        self.access_token = access_token
        self.sid = sid
        self.url = url
        self.heartbeat_interval = heartbeat_interval
        self.reconnect_delay = reconnect_delay
        self.max_reconnect_attempts = max_reconnect_attempts

        self._ws: WebSocketClientProtocol | None = None
        self._connected = False
        self._authenticated = False
        self._heartbeat_task: asyncio.Task | None = None
        self._receive_task: asyncio.Task | None = None
        self._message_queue: asyncio.Queue[SFeedMessage] = asyncio.Queue()
        self._subscribed_tokens: set[WsToken] = set()
        self._reconnect_count = 0

        # Callbacks (for backward compatibility)
        self.on_message: Callable[[SFeedMessage], None] | None = None
        self.on_error: Callable[[Exception], None] | None = None
        self.on_connect: Callable[[], None] | None = None
        self.on_disconnect: Callable[[], None] | None = None

    async def __aenter__(self):
        """Context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.close()

    def __aiter__(self) -> AsyncIterator[SFeedMessage]:
        """Make client async iterable."""
        return self

    async def __anext__(self) -> SFeedMessage:
        """Get next message from queue."""
        if not self._connected:
            raise NotConnectedError("WebSocket is not connected")

        try:
            # Wait for message with timeout to check connection status
            message = await asyncio.wait_for(self._message_queue.get(), timeout=1.0)
            return message
        except asyncio.TimeoutError:
            # Check if still connected
            if not self._connected:
                raise StopAsyncIteration from None
            # Continue waiting
            return await self.__anext__()

    @property
    def is_connected(self) -> bool:
        """Check if WebSocket is connected."""
        return self._connected and self._ws is not None and not self._ws.closed

    async def connect(self) -> None:
        """Connect to Srishti WebSocket and authenticate.

        Raises:
            AlreadyConnectedError: If already connected
            ConnectionError: If connection fails
            AuthenticationError: If authentication fails
        """
        if self.is_connected:
            raise AlreadyConnectedError("WebSocket is already connected")

        try:
            # Create SSL context (disable cert verification for now - TODO: enable in production)
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            # Connect to WebSocket
            self._ws = await websockets.connect(
                self.url,
                ssl=ssl_context,
                ping_interval=None,  # We'll handle heartbeat manually
            )
            self._connected = True

            # Authenticate
            await self._authenticate()

            # Start heartbeat and message receiver
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            self._receive_task = asyncio.create_task(self._receive_loop())

            # Reset reconnect counter on successful connection
            self._reconnect_count = 0

            if self.on_connect:
                self.on_connect()

        except Exception as e:
            self._connected = False
            raise ConnectionError(f"Failed to connect: {e}") from e

    async def _authenticate(self) -> None:
        """Send authentication message.

        Raises:
            AuthenticationError: If authentication fails
        """
        auth_message = {
            "type": "cn",  # connection
            "Authorization": self.access_token,
            "Sid": self.sid,
        }

        try:
            await self._ws.send(json.dumps(auth_message))

            # Wait for auth response (TODO: Adjust based on actual Srishti protocol)
            response = await asyncio.wait_for(self._ws.recv(), timeout=10.0)
            json.loads(response) if isinstance(response, str) else response

            # TODO: Validate auth response format
            # For now, assume success if we get any response
            self._authenticated = True

        except asyncio.TimeoutError:
            raise AuthenticationError("Authentication timeout") from None
        except Exception as e:
            raise AuthenticationError(f"Authentication failed: {e}") from e

    async def _heartbeat_loop(self) -> None:
        """Send periodic heartbeat messages."""
        while self.is_connected:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                if self.is_connected:
                    heartbeat = {"type": "hb"}  # heartbeat
                    await self._ws.send(json.dumps(heartbeat))
            except Exception as e:
                if self.on_error:
                    self.on_error(e)
                break

    async def _receive_loop(self) -> None:
        """Receive and parse messages from WebSocket."""
        while self.is_connected:
            try:
                raw_message = await self._ws.recv()

                # Parse message
                message = self._parse_message(raw_message)
                if message:
                    # Put in queue for async iteration
                    await self._message_queue.put(message)

                    # Call callback if set (for backward compatibility)
                    if self.on_message:
                        self.on_message(message)

            except websockets.exceptions.ConnectionClosed:
                self._connected = False
                await self._handle_disconnect()
                break
            except Exception as e:
                if self.on_error:
                    self.on_error(e)

    def _parse_message(self, raw_message: Any) -> SFeedMessage | None:
        """Parse raw message to Pydantic model.

        Args:
            raw_message: Raw message from WebSocket

        Returns:
            Parsed message or None if not a data message

        Raises:
            MessageParseError: If message cannot be parsed
        """
        try:
            # Handle string JSON messages
            if isinstance(raw_message, str):
                data = json.loads(raw_message)
            elif isinstance(raw_message, bytes):
                # TODO: Handle binary messages if Srishti uses binary protocol
                data = json.loads(raw_message.decode("utf-8"))
            else:
                data = raw_message

            # Skip system messages (heartbeat acks, etc.)
            if isinstance(data, dict) and "type" in data:
                msg_type = data.get("type")

                # Map message type to model
                if msg_type == "scrip":
                    return SFeedScrip(**data)
                elif msg_type == "scrip_lite":
                    return SFeedScripLite(**data)
                elif msg_type == "index":
                    return SFeedIndex(**data)
                elif msg_type == "depth":
                    return SFeedDepth(**data)
                # Ignore system messages
                elif msg_type in ("hb", "ack", "cn"):
                    return None

            return None

        except ValidationError as e:
            raise MessageParseError(f"Invalid message format: {e}") from e
        except Exception as e:
            raise MessageParseError(f"Failed to parse message: {e}") from e

    async def _handle_disconnect(self) -> None:
        """Handle unexpected disconnection and attempt reconnection."""
        self._connected = False

        if self.on_disconnect:
            self.on_disconnect()

        # Attempt reconnection
        if self._reconnect_count < self.max_reconnect_attempts:
            self._reconnect_count += 1
            await asyncio.sleep(self.reconnect_delay)

            try:
                await self.connect()

                # Re-subscribe to previous tokens
                if self._subscribed_tokens:
                    await self.subscribe_scrips(list(self._subscribed_tokens))

            except Exception as e:
                if self.on_error:
                    self.on_error(e)
                # Retry again
                await self._handle_disconnect()

    async def subscribe_scrips(
        self,
        tokens: list[WsToken],
        mode: str = "full",
    ) -> None:
        """Subscribe to scrip data.

        Args:
            tokens: List of WsToken to subscribe
            mode: Subscription mode - 'full' or 'lite' (default: 'full')

        Raises:
            NotConnectedError: If not connected
            SubscriptionError: If subscription fails
        """
        if not self.is_connected:
            raise NotConnectedError("WebSocket is not connected")

        try:
            # TODO: Update payload format based on actual Srishti protocol
            subscribe_message = {
                "type": "mws",  # market watch subscribe
                "scrips": [
                    {"exchangeSegment": token.exchange_segment, "token": token.instrument_token}
                    for token in tokens
                ],
                "channelnum": 1,
                "mode": mode,
            }

            await self._ws.send(json.dumps(subscribe_message))

            # Store subscribed tokens for reconnection
            self._subscribed_tokens.update(tokens)

        except Exception as e:
            raise SubscriptionError(f"Failed to subscribe: {e}") from e

    async def unsubscribe_scrips(self, tokens: list[WsToken]) -> None:
        """Unsubscribe from scrip data.

        Args:
            tokens: List of WsToken to unsubscribe

        Raises:
            NotConnectedError: If not connected
            SubscriptionError: If unsubscription fails
        """
        if not self.is_connected:
            raise NotConnectedError("WebSocket is not connected")

        try:
            # TODO: Update payload format based on actual Srishti protocol
            unsubscribe_message = {
                "type": "mwu",  # market watch unsubscribe
                "scrips": [
                    {"exchangeSegment": token.exchange_segment, "token": token.instrument_token}
                    for token in tokens
                ],
                "channelnum": 1,
            }

            await self._ws.send(json.dumps(unsubscribe_message))

            # Remove from subscribed tokens
            self._subscribed_tokens.difference_update(tokens)

        except Exception as e:
            raise SubscriptionError(f"Failed to unsubscribe: {e}") from e

    async def subscribe_index(self, tokens: list[WsToken]) -> None:
        """Subscribe to index data.

        Args:
            tokens: List of WsToken to subscribe

        Raises:
            NotConnectedError: If not connected
            SubscriptionError: If subscription fails
        """
        if not self.is_connected:
            raise NotConnectedError("WebSocket is not connected")

        try:
            # TODO: Update payload format based on actual Srishti protocol
            subscribe_message = {
                "type": "ifs",  # index feed subscribe
                "scrips": [
                    {"exchangeSegment": token.exchange_segment, "token": token.instrument_token}
                    for token in tokens
                ],
                "channelnum": 1,
            }

            await self._ws.send(json.dumps(subscribe_message))
            self._subscribed_tokens.update(tokens)

        except Exception as e:
            raise SubscriptionError(f"Failed to subscribe to index: {e}") from e

    async def subscribe_depth(self, tokens: list[WsToken]) -> None:
        """Subscribe to market depth data.

        Args:
            tokens: List of WsToken to subscribe

        Raises:
            NotConnectedError: If not connected
            SubscriptionError: If subscription fails
        """
        if not self.is_connected:
            raise NotConnectedError("WebSocket is not connected")

        try:
            # TODO: Update payload format based on actual Srishti protocol
            subscribe_message = {
                "type": "dps",  # depth subscribe
                "scrips": [
                    {"exchangeSegment": token.exchange_segment, "token": token.instrument_token}
                    for token in tokens
                ],
                "channelnum": 1,
            }

            await self._ws.send(json.dumps(subscribe_message))
            self._subscribed_tokens.update(tokens)

        except Exception as e:
            raise SubscriptionError(f"Failed to subscribe to depth: {e}") from e

    async def close(self) -> None:
        """Close WebSocket connection and cleanup resources."""
        self._connected = False
        self._authenticated = False

        # Cancel tasks
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._heartbeat_task

        if self._receive_task:
            self._receive_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._receive_task

        # Close WebSocket
        if self._ws:
            await self._ws.close()
            self._ws = None

        if self.on_disconnect:
            self.on_disconnect()
