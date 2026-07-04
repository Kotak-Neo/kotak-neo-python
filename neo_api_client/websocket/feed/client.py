"""Modern async/await WebSocket client for the SFeed market-data feed.

Implements the ``native_batch`` protocol:

* Control plane — JSON text frames (auth, subscribe, unsubscribe, snapshot).
* Data plane — binary frames (little-endian, packed, batched); decoded by
  :mod:`neo_api_client.websocket.feed.protocol`.

There is no application-level heartbeat in this mode; the WebSocket layer's
native ping/pong keeps the connection alive.
"""

import asyncio
import contextlib
import json
import ssl
import time
from collections.abc import AsyncIterator, Callable
from typing import Any

import websockets

from neo_api_client.utils.urls import SFEED_WEBSOCKET_URL
from neo_api_client.websocket.feed.exceptions import (
    AlreadyConnectedError,
    AuthenticationError,
    ConnectionError,
    NotConnectedError,
    SubscriptionError,
)
from neo_api_client.websocket.feed.models import (
    EXCHANGE_NAME_TO_ID,
    SFeedMessage,
    WsToken,
)
from neo_api_client.websocket.feed.protocol import (
    MSG_AUTH_RESPONSE_CODES,
    decode_packet,
    split_batch,
)

# Control-plane event names by subscription intent (see protocol §3.1).
_SUBSCRIBE_EVENTS = {
    "scrips": "subscribeScrips",
    "scrips_lite": "subscribeScripsLite",
    "depth": "subscribeDepth",
    "full_depth": "subscribeFullDepth",
    "index": "subscribeIndices",
}
_UNSUBSCRIBE_EVENTS = {
    "scrips": "unsubscribeScrips",
    "scrips_lite": "unsubscribeScripsLite",
    "depth": "unsubscribeDepth",
    "full_depth": "unsubscribeFullDepth",
    "index": "unsubscribeIndices",
}
_SNAPSHOT_EVENTS = {
    "scrips": "snapshotScrips",
    "scrips_lite": "snapshotScripsLite",
    "depth": "snapshotDepth",
    "index": "snapshotIndices",
}


class SFeedWebSocket:
    """Async/await WebSocket client for the SFeed ``native_batch`` feed.

    Example:
        ```python
        async with SFeedWebSocket(user="U", auth="TOKEN") as ws:
            await ws.subscribe_scrips([WsToken("nse_cm", "11536")])
            async for message in ws:
                print(type(message).__name__, message.model_dump())
        ```
    """

    def __init__(
        self,
        access_token: str | None = None,
        sid: str | None = None,
        url: str = SFEED_WEBSOCKET_URL,
        *,
        user: str = "neome",
        auth: str = "1",
        source: str = "SFeed",
        platform: str = "Web",
        version: str = "1.2.3",
        sdk_version: int = 2,
        sdk_date: str = "2026-05-21T09:35:34.304Z",
        session_validation: bool = False,
        reconnect_delay: int = 5,
        max_reconnect_attempts: int = 5,
        ping_interval: int = 20,
        max_subscriptions: int = 3000,
    ):
        """Initialize the client.

        Args:
            access_token: Session token (retained for compatibility; the feed
                uses the ``user``/``auth`` credentials below, not this token).
            sid: Session id (retained for compatibility).
            url: Feed URL (default: SFeed production ``/wsfeed``).
            user: ``user`` credential for the native_batch auth frame.
            auth: ``auth`` credential for the native_batch auth frame.
            source: Client identification (default 'SFeed').
            platform: Client platform string (default 'Web').
            version: Client version string sent in the auth frame.
            sdk_version: SDK/build version integer sent in the auth frame.
            sdk_date: SDK/build date string sent in the auth frame.
            session_validation: Value for the ``sessionValidation`` auth field.
            reconnect_delay: Seconds between reconnect attempts.
            max_reconnect_attempts: Maximum reconnect attempts.
            ping_interval: WebSocket-level ping interval (keep-alive) in seconds.
            max_subscriptions: Maximum total input tokens that may be subscribed
                at once across all subscribe requests (LTP, option chain, etc.).
                Default 3000. A request that would exceed this raises
                :class:`SubscriptionError`.
        """
        self.access_token = access_token
        self.sid = sid
        self.url = url
        self.user = user
        self.auth = auth
        self.source = source
        self.platform = platform
        self.version = version
        self.sdk_version = sdk_version
        self.sdk_date = sdk_date
        self.session_validation = session_validation
        self.reconnect_delay = reconnect_delay
        self.max_reconnect_attempts = max_reconnect_attempts
        self.ping_interval = ping_interval
        self.max_subscriptions = max_subscriptions

        self._ws: Any = None
        self._connected = False
        self._authenticated = False
        self._receive_task: asyncio.Task | None = None
        self._message_queue: asyncio.Queue[SFeedMessage] = asyncio.Queue()
        # Remember (token, intent) so we can re-subscribe after a reconnect.
        self._subscriptions: set[tuple[WsToken, str]] = set()
        self._reconnect_count = 0
        # Price dividers keyed by exchange_id (from the auth response).
        self._dividers: dict[int, int] = {}

        # Callbacks
        self.on_message: Callable[[SFeedMessage], None] | None = None
        self.on_error: Callable[[Exception], None] | None = None
        self.on_connect: Callable[[], None] | None = None
        self.on_disconnect: Callable[[], None] | None = None
        # Raw-frame hook: every frame (str or bytes) before parsing (debugging).
        self.on_raw: Callable[[str | bytes], None] | None = None

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    def __aiter__(self) -> AsyncIterator[SFeedMessage]:
        return self

    async def __anext__(self) -> SFeedMessage:
        if not self._connected:
            raise NotConnectedError("WebSocket is not connected")
        try:
            return await asyncio.wait_for(self._message_queue.get(), timeout=1.0)
        except asyncio.TimeoutError:
            if not self._connected:
                raise StopAsyncIteration from None
            return await self.__anext__()

    @property
    def is_connected(self) -> bool:
        """Whether the socket is open."""
        if not self._connected or self._ws is None:
            return False
        closed = getattr(self._ws, "closed", None)
        if closed is not None:
            return not closed
        state = getattr(self._ws, "state", None)
        if state is not None:
            return getattr(state, "name", None) == "OPEN"
        return True

    @property
    def dividers(self) -> dict[int, int]:
        """Per-exchange price dividers (keyed by exchange_id) from auth."""
        return dict(self._dividers)

    @property
    def subscription_count(self) -> int:
        """Total number of currently subscribed input tokens across all requests."""
        return len(self._subscriptions)

    async def connect(self) -> None:
        """Open the socket and authenticate.

        Raises:
            AlreadyConnectedError: If already connected.
            ConnectionError: If the socket fails to open.
            AuthenticationError: If authentication fails.
        """
        if self.is_connected:
            raise AlreadyConnectedError("WebSocket is already connected")

        try:
            ssl_context = None
            if self.url.startswith("wss"):
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE

            self._ws = await websockets.connect(
                self.url,
                ssl=ssl_context,
                # Rely on the WebSocket layer's native ping/pong for keep-alive.
                ping_interval=self.ping_interval,
            )
            self._connected = True
        except Exception as e:
            self._connected = False
            raise ConnectionError(f"Failed to connect: {e}") from e

        # Authenticate (may raise AuthenticationError).
        await self._authenticate()

        # Start the receive loop and reset reconnect state.
        self._receive_task = asyncio.create_task(self._receive_loop())
        self._reconnect_count = 0
        if self.on_connect:
            self.on_connect()

    def _build_auth_frame(self) -> dict:
        """Build the native_batch authentication frame."""
        return {
            "user": self.user,
            "auth": self.auth,
            "format": "native_batch",
            "source": self.source,
            "platform": self.platform,
            "version": self.version,
            "sdk_version": self.sdk_version,
            "sdk_date": self.sdk_date,
            "conn_req_time": int(time.time() * 1000),
            "sessionValidation": self.session_validation,
        }

    async def _authenticate(self) -> None:
        """Send the native_batch auth frame and store the per-exchange dividers.

        Raises:
            AuthenticationError: On timeout, bad response, or a fallback downgrade.
        """
        try:
            await self._ws.send(json.dumps(self._build_auth_frame()))

            # The auth response is a JSON text frame (message_code 1117 or 1119).
            # Skip any binary frames that may arrive before it.
            data = None
            for _ in range(10):
                raw = await asyncio.wait_for(self._ws.recv(), timeout=10.0)
                if isinstance(raw, str):
                    data = json.loads(raw)
                    break
            if data is None or data.get("message_code") not in MSG_AUTH_RESPONSE_CODES:
                raise AuthenticationError(f"Unexpected auth response: {data!r}")

            fmt = data.get("format")
            if fmt == "native_fallback":
                raise AuthenticationError("Server downgraded to native_fallback (out of scope)")

            # Persist dividers keyed by exchange_id for binary decoding.
            # Prefer the exchange_id from the response's own "value" field,
            # falling back to our static name->id map.
            self._dividers = {}
            for name, info in (data.get("exchanges") or {}).items():
                if not isinstance(info, dict):
                    continue
                exch_id = info.get("value", EXCHANGE_NAME_TO_ID.get(name))
                if exch_id is not None:
                    self._dividers[int(exch_id)] = info.get("divider", 100)

            self._authenticated = True
        except AuthenticationError:
            raise
        except asyncio.TimeoutError:
            raise AuthenticationError("Authentication timeout") from None
        except Exception as e:
            raise AuthenticationError(f"Authentication failed: {e}") from e

    async def _receive_loop(self) -> None:
        """Receive frames, de-frame binary batches, decode, and enqueue."""
        while self.is_connected:
            try:
                raw = await self._ws.recv()

                if self.on_raw:
                    with contextlib.suppress(Exception):
                        self.on_raw(raw)

                if isinstance(raw, (bytes, bytearray)):
                    self._handle_binary_frame(bytes(raw))
                # JSON text frames after auth are control acks / status; ignore.

            except websockets.exceptions.ConnectionClosed:
                self._connected = False
                await self._handle_disconnect()
                break
            except Exception as e:  # pragma: no cover - defensive
                if self.on_error:
                    self.on_error(e)

    def _handle_binary_frame(self, frame: bytes) -> None:
        """Split a binary batch into packets, decode each, and enqueue."""
        for packet in split_batch(frame):
            try:
                message = decode_packet(packet, self._dividers)
            except Exception as e:  # pragma: no cover - defensive
                if self.on_error:
                    self.on_error(e)
                continue
            if message is None:
                continue
            self._message_queue.put_nowait(message)
            if self.on_message:
                with contextlib.suppress(Exception):
                    self.on_message(message)

    async def _handle_disconnect(self) -> None:
        """Reconnect from scratch and re-send all subscriptions."""
        self._connected = False
        if self.on_disconnect:
            self.on_disconnect()

        if self._reconnect_count >= self.max_reconnect_attempts:
            return
        self._reconnect_count += 1
        await asyncio.sleep(self.reconnect_delay)

        try:
            await self.connect()
            # Re-send every remembered subscription (server forgets on close),
            # grouped by intent so each group goes out as one batched frame.
            by_intent: dict[str, list[WsToken]] = {}
            for token, intent in list(self._subscriptions):
                by_intent.setdefault(intent, []).append(token)
            for intent, tokens in by_intent.items():
                await self._send_subscribe(_SUBSCRIBE_EVENTS[intent], tokens)
        except Exception as e:
            if self.on_error:
                self.on_error(e)
            await self._handle_disconnect()

    @staticmethod
    def _inputtoken(tokens: list[WsToken]) -> str:
        """Build the comma-separated ``<exchange>|<token>`` list for a frame."""
        return ",".join(t.inputtoken for t in tokens)

    async def _send_subscribe(self, event: str, tokens: list[WsToken]) -> None:
        """Send a batched subscribe frame (all tokens in one ``inputtoken``)."""
        await self._ws.send(
            json.dumps({"event": event, "inputtoken": self._inputtoken(tokens), "json": "false"})
        )

    async def _send_unsubscribe(self, event: str, tokens: list[WsToken]) -> None:
        """Send a batched unsubscribe frame (no ``json`` field, per spec)."""
        await self._ws.send(json.dumps({"event": event, "inputtoken": self._inputtoken(tokens)}))

    async def _subscribe(self, tokens: list[WsToken], intent: str) -> None:
        if not self.is_connected:
            raise NotConnectedError("WebSocket is not connected")
        if not tokens:
            return

        # Enforce the total subscription cap across all requests (LTP, option
        # chain, etc.). Count only tokens that are not already subscribed for
        # this intent, and reject the whole request before sending anything.
        new_pairs = {(token, intent) for token in tokens} - self._subscriptions
        projected_total = len(self._subscriptions) + len(new_pairs)
        if projected_total > self.max_subscriptions:
            raise SubscriptionError(
                f"Subscription limit exceeded: {projected_total} tokens requested "
                f"(currently {len(self._subscriptions)}, adding {len(new_pairs)} new), "
                f"but the maximum is {self.max_subscriptions}."
            )

        try:
            await self._send_subscribe(_SUBSCRIBE_EVENTS[intent], tokens)
            self._subscriptions.update(new_pairs)
        except SubscriptionError:
            raise
        except Exception as e:
            raise SubscriptionError(f"Failed to subscribe ({intent}): {e}") from e

    async def _unsubscribe(self, tokens: list[WsToken], intent: str) -> None:
        if not self.is_connected:
            raise NotConnectedError("WebSocket is not connected")
        if not tokens:
            return
        try:
            await self._send_unsubscribe(_UNSUBSCRIBE_EVENTS[intent], tokens)
            for token in tokens:
                self._subscriptions.discard((token, intent))
        except Exception as e:
            raise SubscriptionError(f"Failed to unsubscribe ({intent}): {e}") from e

    # ---- Public subscription API -------------------------------------------

    async def subscribe_scrips(self, tokens: list[WsToken]) -> None:
        """Subscribe to touch-line market data (level 4)."""
        await self._subscribe(tokens, "scrips")

    async def unsubscribe_scrips(self, tokens: list[WsToken]) -> None:
        """Unsubscribe from touch-line market data."""
        await self._unsubscribe(tokens, "scrips")

    async def subscribe_scrips_lite(self, tokens: list[WsToken]) -> None:
        """Subscribe to mini touch-line market data (level 1)."""
        await self._subscribe(tokens, "scrips_lite")

    async def unsubscribe_scrips_lite(self, tokens: list[WsToken]) -> None:
        """Unsubscribe from mini touch-line market data."""
        await self._unsubscribe(tokens, "scrips_lite")

    async def subscribe_depth(self, tokens: list[WsToken]) -> None:
        """Subscribe to market depth (level 8)."""
        await self._subscribe(tokens, "depth")

    async def unsubscribe_depth(self, tokens: list[WsToken]) -> None:
        """Unsubscribe from market depth."""
        await self._unsubscribe(tokens, "depth")

    async def subscribe_full_depth(self, tokens: list[WsToken]) -> None:
        """Subscribe to full market depth (level 16)."""
        await self._subscribe(tokens, "full_depth")

    async def unsubscribe_full_depth(self, tokens: list[WsToken]) -> None:
        """Unsubscribe from full market depth."""
        await self._unsubscribe(tokens, "full_depth")

    async def subscribe_index(self, tokens: list[WsToken]) -> None:
        """Subscribe to index data."""
        await self._subscribe(tokens, "index")

    async def unsubscribe_index(self, tokens: list[WsToken]) -> None:
        """Unsubscribe from index data."""
        await self._unsubscribe(tokens, "index")

    async def snapshot(self, tokens: list[WsToken], intent: str = "scrips") -> None:
        """Request a one-time snapshot. Reply arrives on the live binary feed.

        Args:
            tokens: Instruments to snapshot.
            intent: One of 'scrips', 'scrips_lite', 'depth', 'index'.
        """
        if not self.is_connected:
            raise NotConnectedError("WebSocket is not connected")
        if not tokens:
            return
        event = _SNAPSHOT_EVENTS.get(intent)
        if event is None:
            raise SubscriptionError(f"Snapshot not supported for intent '{intent}'")
        try:
            await self._send_subscribe(event, tokens)
        except Exception as e:
            raise SubscriptionError(f"Failed to snapshot ({intent}): {e}") from e

    async def close(self) -> None:
        """Close the socket and clean up."""
        self._connected = False
        self._authenticated = False

        if self._receive_task:
            self._receive_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._receive_task
            self._receive_task = None

        if self._ws:
            await self._ws.close()
            self._ws = None

        if self.on_disconnect:
            self.on_disconnect()
