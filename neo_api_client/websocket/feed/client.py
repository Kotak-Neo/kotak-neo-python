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
import warnings
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
    MSG_SUBSCRIBE_ACK,
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
        max_connect_retries: int = 3,
        ping_interval: int = 20,
        max_subscriptions: int = 3000,
        verify_ssl: bool = True,
        ack_wait_timeout: float = 5.0,
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
            reconnect_delay: Seconds between reconnect attempts (also used
                between initial connect retries, see ``max_connect_retries``).
            max_reconnect_attempts: Maximum number of times to reconnect after
                a previously established connection later drops.
            max_connect_retries: Maximum number of retries for the *initial*
                ``connect()`` call itself if opening the socket fails (e.g. a
                transient network error) — separate from
                ``max_reconnect_attempts``, which only applies after a
                connection has already succeeded once. Default 3. Set to 0
                to fail immediately on the first attempt, with no retries.
            ping_interval: WebSocket-level ping interval (keep-alive) in seconds.
            max_subscriptions: Maximum total input tokens that may be subscribed
                at once across all subscribe requests (LTP, option chain, etc.).
                Default 3000. A request that would exceed this raises
                :class:`SubscriptionError`.
            verify_ssl: Verify the server's TLS certificate on ``wss://``
                connections (default True). Only set to False for a trusted
                development endpoint with a self-signed certificate; disabling
                verification exposes the connection to man-in-the-middle attacks.
            ack_wait_timeout: Seconds to wait for the server's subscribe
                acknowledgement (message_code 1109, carrying the
                trading_symbols map) after sending a subscribe frame.
                Default 5.0. While an ack is outstanding, incoming data
                frames are **discarded** rather than decoded/delivered —
                this is a live price feed, so a tick decoded before its
                trading_symbol mapping was known can't be held back and
                delivered later without going stale relative to newer
                ticks; dropping it is preferable to that. See
                ``dropped_frame_count``. ``subscribe_scrips()`` (etc.) also
                waits up to this long before returning. If no ack arrives
                within the timeout, frames stop being discarded (delivered
                with ``trading_symbol=None`` where unmapped) and the
                subscribe call returns anyway — the feed never stalls
                indefinitely on a missing ack.
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
        self.max_connect_retries = max_connect_retries
        self.ping_interval = ping_interval
        self.max_subscriptions = max_subscriptions
        self.verify_ssl = verify_ssl

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
        # Trading-symbol map keyed by "<exchange_segment>|<instrument_token>"
        # (e.g. "nse_cm|2885" -> "RELIANCE-EQ"), built from the subscribe
        # acknowledgement (message_code 1109) and cleared on unsubscribe. Used
        # to enrich each feed message with its trading_symbol.
        self._trading_symbols: dict[str, str] = {}
        # Signaled by _handle_text_frame whenever a subscribe acknowledgement
        # is processed. _wait_for_subscribe_ack waits on this (briefly) so a
        # subscribe call doesn't return to the caller before trading_symbols
        # is populated.
        self._subscribe_ack_event = asyncio.Event()
        self.ack_wait_timeout = ack_wait_timeout
        # While True, _handle_binary_frame drops incoming frames instead of
        # decoding/delivering them. Set by _send_subscribe (a subscribe was
        # just sent, ack_symbol requested) and cleared once the ack is
        # processed — or once ack_deadline passes, so a lost/delayed ack
        # can't block the live feed forever. This is a live market price
        # feed: a data frame that arrives before its trading_symbol mapping
        # is known cannot be buffered and delivered later, since that would
        # deliver a stale price out of order with newer ticks. Discarding it
        # is correct — the next frame for that token supersedes it anyway.
        self._ack_pending = False
        self._ack_deadline: float | None = None
        self._dropped_frame_count = 0

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
    def trading_symbols(self) -> dict[str, str]:
        """Trading-symbol map (``"<exchange>|<token>"`` -> symbol) from the
        subscribe acknowledgement. Grows on subscribe, shrinks on unsubscribe."""
        return dict(self._trading_symbols)

    @property
    def subscription_count(self) -> int:
        """Total number of currently subscribed input tokens across all requests."""
        return len(self._subscriptions)

    @property
    def dropped_frame_count(self) -> int:
        """Total binary frames discarded because they arrived before a
        subscribe acknowledgement (see ``ack_wait_timeout``)."""
        return self._dropped_frame_count

    async def connect(self) -> None:
        """Open the socket and authenticate.

        Opening the socket itself is retried up to ``max_connect_retries``
        times (waiting ``reconnect_delay`` seconds between attempts) if it
        fails — e.g. a transient network error on the very first connect.
        This is separate from the post-connect auto-reconnect handled by
        ``max_reconnect_attempts``, and doesn't cover authentication: an
        ``AuthenticationError`` usually isn't transient, so it's raised
        immediately without retrying.

        Raises:
            AlreadyConnectedError: If already connected.
            ConnectionError: If the socket fails to open after all retries.
            AuthenticationError: If authentication fails.
        """
        if self.is_connected:
            raise AlreadyConnectedError("WebSocket is already connected")

        # Discard any state left over from a prior connection (e.g. an
        # ack-pending window that never resolved before a disconnect) — it
        # doesn't apply to the connection being opened now.
        self._ack_pending = False
        self._ack_deadline = None

        ssl_context = None
        if self.url.startswith("wss"):
            ssl_context = ssl.create_default_context()
            if not self.verify_ssl:
                # Insecure: only for a trusted dev endpoint with a
                # self-signed cert. Disables MITM protection.
                warnings.warn(
                    "TLS certificate verification is disabled for the SFeed "
                    "WebSocket (verify_ssl=False); the connection is exposed "
                    "to man-in-the-middle attacks. Do not use in production.",
                    stacklevel=2,
                )
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE

        connect_error = None
        for attempt in range(self.max_connect_retries + 1):
            try:
                self._ws = await websockets.connect(
                    self.url,
                    ssl=ssl_context,
                    # Rely on the WebSocket layer's native ping/pong for keep-alive.
                    ping_interval=self.ping_interval,
                )
                self._connected = True
                connect_error = None
                break
            except Exception as e:
                self._connected = False
                connect_error = e
                if attempt < self.max_connect_retries:
                    await asyncio.sleep(self.reconnect_delay)

        if connect_error is not None:
            raise ConnectionError(
                f"Failed to connect after {self.max_connect_retries + 1} attempt(s): "
                f"{connect_error}"
            ) from connect_error

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
                else:
                    # JSON text frame — the subscribe acknowledgement carries the
                    # trading_symbols map; other control frames are ignored.
                    self._handle_text_frame(raw)

            except websockets.exceptions.ConnectionClosed:
                self._connected = False
                await self._handle_disconnect()
                break
            except Exception as e:  # pragma: no cover - defensive
                if self.on_error:
                    self.on_error(e)

    def _handle_text_frame(self, raw: str | bytes) -> None:
        """Handle a JSON control frame.

        The subscribe acknowledgement (``message_code`` 1109) carries a
        ``trading_symbols`` map keyed by ``"<exchange>|<token>"``; record it so
        subsequent feed messages can be enriched with their trading_symbol.
        Any other control frame is ignored.
        """
        try:
            data = json.loads(raw)
        except (ValueError, TypeError):
            return
        if not isinstance(data, dict):
            return
        if data.get("message_code") == MSG_SUBSCRIBE_ACK:
            mapping = data.get("trading_symbols")
            if isinstance(mapping, dict):
                for key, symbol in mapping.items():
                    if isinstance(key, str) and isinstance(symbol, str):
                        self._trading_symbols[key] = symbol
            # Wake up any _wait_for_subscribe_ack() waiting on this ack.
            # Set/clear around each subscribe send (see _send_subscribe) so a
            # later ack doesn't spuriously satisfy an earlier wait that
            # already timed out.
            self._subscribe_ack_event.set()
            # The map is now up to date -- resume decoding/delivering frames.
            self._ack_pending = False
            self._ack_deadline = None

    def _trading_symbol_for(self, message: SFeedMessage) -> str | None:
        """Look up the trading symbol for a decoded message, if known."""
        key = f"{message.exchange_segment}|{message.instrument_token}"
        return self._trading_symbols.get(key)

    def _ack_deadline_passed(self) -> bool:
        return self._ack_deadline is not None and time.monotonic() >= self._ack_deadline

    def _handle_binary_frame(self, frame: bytes) -> None:
        """Split a binary batch into packets, decode each, and enqueue.

        While a subscribe acknowledgement is outstanding (``_ack_pending``),
        incoming frames are **discarded**, not buffered. This is a live
        market price feed: a tick that arrived before its trading_symbol
        mapping was known cannot be held back and delivered later, since
        that would deliver a stale price out of order relative to newer
        ticks arriving once the ack lands — worse than a brief gap. The next
        frame for that token (post-ack) supersedes whatever was dropped.

        If the ack doesn't arrive within ``ack_wait_timeout``, frames stop
        being discarded even without one (server may not always send acks,
        or may be slow) so the feed doesn't stall indefinitely.
        """
        if self._ack_pending:
            if self._ack_deadline_passed():
                self._ack_pending = False
                self._ack_deadline = None
            else:
                self._dropped_frame_count += 1
                return
        self._decode_and_deliver_binary_frame(frame)

    def _decode_and_deliver_binary_frame(self, frame: bytes) -> None:
        """Decode a binary batch into packets and enqueue/deliver each message."""
        for packet in split_batch(frame):
            try:
                message = decode_packet(packet, self._dividers)
            except Exception as e:  # pragma: no cover - defensive
                if self.on_error:
                    self.on_error(e)
                continue
            if message is None:
                continue
            # Enrich with the trading symbol resolved from the subscribe ack.
            symbol = self._trading_symbol_for(message)
            if symbol is not None:
                message.trading_symbol = symbol
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
        """Send a batched subscribe frame (all tokens in one ``inputtoken``).

        ``ack_symbol: true`` asks the server to return the trading-symbol
        acknowledgement (message_code 1109) mapping each ``exchange|token`` to
        its trading symbol, which enriches subsequent feed messages.

        Data frames delivered by the receive loop while this ack is
        outstanding are held back (see ``_handle_binary_frame`` /
        ``_ack_pending``) so they aren't decoded and delivered with
        ``trading_symbol=None`` before the map is ready.
        """
        self._subscribe_ack_event.clear()
        self._ack_pending = True
        self._ack_deadline = time.monotonic() + self.ack_wait_timeout
        await self._ws.send(
            json.dumps({
                "event": event,
                "inputtoken": self._inputtoken(tokens),
                "ack_symbol": True,
            })
        )

    async def _wait_for_subscribe_ack(self) -> None:
        """Wait briefly for the subscribe acknowledgement sent by ``_send_subscribe``.

        Closes a race where the server's binary data frames for the just-
        subscribed tokens arrive on ``_receive_loop`` before the ack —
        without this wait, those frames would be enriched with
        ``trading_symbol=None`` permanently, since enrichment only happens
        once, at decode time (see ``_handle_binary_frame``).

        Only waits if the receive loop is actually running to process an
        ack — without it (e.g. before connect(), or in tests that stub the
        socket directly) no ack could ever arrive, so waiting would just
        block for the full timeout with nothing to show for it. Must be
        called *after* ``self._subscriptions`` bookkeeping is updated, so a
        disconnect/reconnect racing this wait still has the correct
        subscription set to resend.
        """
        if self._receive_task is not None:
            with contextlib.suppress(asyncio.TimeoutError):
                await asyncio.wait_for(
                    self._subscribe_ack_event.wait(), timeout=self.ack_wait_timeout
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

        await self._wait_for_subscribe_ack()

    async def _unsubscribe(self, tokens: list[WsToken], intent: str) -> None:
        if not self.is_connected:
            raise NotConnectedError("WebSocket is not connected")
        if not tokens:
            return
        try:
            await self._send_unsubscribe(_UNSUBSCRIBE_EVENTS[intent], tokens)
            for token in tokens:
                self._subscriptions.discard((token, intent))
                # Drop the trading-symbol mapping only when the token is no
                # longer subscribed under any intent (it may still be live on
                # another feed level, e.g. depth vs touch line).
                if not any(t == token for t, _ in self._subscriptions):
                    self._trading_symbols.pop(token.inputtoken, None)
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
