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
from neo_api_client.utils.ws_scheme import to_websocket_scheme as _to_websocket_scheme
from neo_api_client.websocket.feed.exceptions import (
    AlreadyConnectedError,
    AuthenticationError,
    ConnectionError,
    NotConnectedError,
    SubscriptionError,
)
from neo_api_client.websocket.feed.models import (
    EXCHANGE_NAME_TO_ID,
    SFeedIndex,
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
        ucc: str | None = None,
        user: str | None = None,
        auth: str | None = None,
        source: str = "NEOTRADEAPI",
        platform: str = "Web",
        version: str = "1.2.3",
        sdk_version: int = 2,
        sdk_date: str = "2026-08-07T09:41:17.667Z",
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
            sid: Session id. Also used as the default ``auth`` credential (see
                ``auth`` below) — some endpoints (e.g. the beta feed) reject
                the connection a few seconds in if ``auth`` doesn't match a
                real session's sid.
            url: Feed URL (default: SFeed production ``/wsfeed``).
            ucc: Unique Client Code (from the totp_login()/totp_validate()
                response). Used as the default ``user`` credential (see
                ``user`` below).
            user: ``user`` credential for the native_batch auth frame.
                Defaults to ``ucc`` when not given; falls back to the demo
                placeholder ``"neome"`` only if ``ucc`` is also not given
                (e.g. constructing without a real session, such as in tests).
            auth: ``auth`` credential for the native_batch auth frame.
                Defaults to ``sid`` when not given; falls back to ``"1"`` only
                if ``sid`` is also not given (e.g. constructing without a real
                session, such as in tests).
            source: Client identification (default 'NEOTRADEAPI').
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
                Default 5.0. While an ack is outstanding, messages for
                instruments whose ``trading_symbol`` is still unknown are
                decoded but their **delivery is withheld**; instruments
                already resolved (from an earlier subscribe) keep streaming
                immediately, unaffected. Withheld messages are kept one per
                ``(instrument, message type/level)`` key — each new message
                for the same key overwrites the previous one, so only the
                latest survives; market-open/close events are never
                withheld, since a later "closed" would otherwise erase an
                earlier "open" instead of both being delivered. In-between
                ticks during the wait are discarded on purpose — the latest
                tick per key is preserved, not every tick — matching a live
                feed where an out-of-date price is superseded the moment a
                newer one arrives; this is not a delta feed, and callers
                that need every individual tick (e.g. for tick-by-tick
                volume/trade-count analytics) should not rely on this
                window. As soon as the ack lands, every held-back key's
                latest message is delivered — enriched with its now-known
                ``trading_symbol`` — and normal per-message delivery resumes
                for that instrument. If no ack arrives within the timeout,
                the same release happens anyway (with ``trading_symbol=None``
                for keys the map has no entry for) so the feed never stalls
                indefinitely on a missing ack — this applies per subscribe
                call, so two overlapping subscribes each get their own
                timeout rather than one release affecting the other's
                unresolved instruments. ``subscribe_scrips()`` (etc.) also
                waits up to this long before returning.
        """
        self.access_token = access_token
        self.sid = sid
        self.ucc = ucc
        self.url = _to_websocket_scheme(url)
        self.user = user if user is not None else (ucc or "neome")
        self.auth = auth if auth is not None else (sid or "1")
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
        # While True, _handle_binary_frame withholds delivery of incoming
        # messages (decoding them, but not enqueuing/calling on_message).
        # Set by _send_subscribe (a subscribe was just sent, ack_symbol
        # requested) and cleared once every outstanding ack is accounted
        # for (see _acks_outstanding) — or once ack_deadline passes, so a
        # lost/delayed ack can't block the live feed forever.
        self._ack_pending = False
        self._ack_deadline: float | None = None
        # Number of subscribe acks sent but not yet resolved (received, or
        # individually timed out via _wait_for_subscribe_ack). Two
        # subscribe calls in flight at once (e.g. the reconnect path, which
        # sends one per feed intent) means two outstanding acks; only when
        # the count reaches zero do we know every in-flight subscribe's
        # trading_symbols have either arrived or been given up on — ending
        # the withholding window on the *first* reply back would flush
        # messages for the *other*, still-unacknowledged subscribe with
        # trading_symbol=None.
        self._acks_outstanding = 0
        # Latest decoded message per "<exchange_segment>|<instrument_token>"
        # key, for messages that arrived while an ack was outstanding. Since
        # this is a live price feed, an out-of-date tick from several
        # messages ago is worthless once newer ticks for the same
        # instrument have arrived — so only the latest per key is kept
        # (each new one overwrites the prior), never a backlog. Delivered
        # (one tick per key, enriched with the now-known trading_symbol) as
        # soon as the ack lands — see _flush_pending_latest_messages.
        self._pending_latest_by_key: dict[str, SFeedMessage] = {}

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
        # A loop, not recursion: on an idle connection with no incoming
        # messages, asyncio.wait_for times out every second indefinitely.
        # A recursive `return await self.__anext__()` here would add one
        # stack frame per timeout and eventually crash with RecursionError
        # after enough uninterrupted silence (the exact number of timeouts
        # before that happens is Python-version/environment-dependent) --
        # this loop keeps the stack flat instead, so it can run indefinitely.
        while True:
            try:
                return await asyncio.wait_for(self._message_queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                if not self._connected:
                    raise StopAsyncIteration from None

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
    def pending_message_count(self) -> int:
        """Number of distinct instruments currently holding a withheld
        latest-message while a subscribe acknowledgement is outstanding
        (see ``ack_wait_timeout``). Zero when no ack is pending."""
        return len(self._pending_latest_by_key)

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
        # ack-pending window that never resolved before a disconnect, or
        # withheld messages from before the disconnect) — it doesn't apply
        # to the connection being opened now.
        self._ack_pending = False
        self._ack_deadline = None
        self._acks_outstanding = 0
        self._pending_latest_by_key = {}

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
            self._acks_outstanding = max(0, self._acks_outstanding - 1)
            if self._acks_outstanding == 0:
                # Only the LAST outstanding ack ends the withholding window.
                # Releasing on the first of several in-flight subscribes
                # (e.g. the reconnect path, which sends one subscribe per
                # feed intent back-to-back with no wait between them) would
                # flush the other batch's messages before ITS
                # trading_symbols have arrived, delivering them with
                # trading_symbol=None -- exactly what this feature exists
                # to prevent.
                self._ack_pending = False
                self._ack_deadline = None
                self._flush_pending_latest_messages()

    def _trading_symbol_for(self, message: SFeedMessage) -> str | None:
        """Look up the trading symbol for a decoded message, if known.

        Indices are subscribed by name (e.g. ``WsToken("nse_cm", "Nifty 50")``),
        not by the numeric ``instrument_token`` the server resolves them to in
        the streamed message -- the subscribe ack's ``trading_symbols`` map is
        keyed by that name, so index messages fall back to a name-keyed lookup
        when the token-keyed one misses.
        """
        key = f"{message.exchange_segment}|{message.instrument_token}"
        symbol = self._trading_symbols.get(key)
        if symbol is None and isinstance(message, SFeedIndex):
            symbol = self._trading_symbols.get(f"{message.exchange_segment}|{message.name}")
        return symbol

    def _ack_deadline_passed(self) -> bool:
        return self._ack_deadline is not None and time.monotonic() >= self._ack_deadline

    def _decode_packet(self, packet: bytes) -> SFeedMessage | None:
        """Decode a single packet, reporting (and swallowing) decode errors."""
        try:
            return decode_packet(packet, self._dividers)
        except Exception as e:  # pragma: no cover - defensive
            if self.on_error:
                self.on_error(e)
            return None

    def _deliver_message(self, message: SFeedMessage) -> None:
        """Enrich a decoded message with its trading_symbol and deliver it."""
        symbol = self._trading_symbol_for(message)
        if symbol is not None:
            message.trading_symbol = symbol
        self._message_queue.put_nowait(message)
        if self.on_message:
            with contextlib.suppress(Exception):
                self.on_message(message)

    def _flush_pending_latest_messages(self) -> None:
        """Deliver the latest withheld message for each instrument, then clear."""
        pending, self._pending_latest_by_key = self._pending_latest_by_key, {}
        for message in pending.values():
            self._deliver_message(message)

    def _pending_key(self, message: SFeedMessage) -> str | None:
        """Parking-space key for a withheld message, or ``None`` to mean
        "never withhold this — deliver it immediately".

        Keyed by exchange+instrument *and* message type/level, not just
        exchange+instrument: the same instrument can be subscribed at
        multiple levels at once (e.g. touch-line and full depth), and each
        level's updates are distinct data, not interchangeable prices — so
        they must not overwrite each other in the "latest wins" map.

        ``market_status`` messages (market open/close) are never withheld:
        they share one key per exchange (their ``instrument_token`` is
        always empty), so "latest wins" would silently drop an "open"
        notice if a "close" notice for the same exchange arrived later in
        the same withholding window — turning a real state transition into
        a single, wrong-looking event. Unlike price ticks, an event isn't
        superseded by a later event; both matter.
        """
        if message.type == "market_status":
            return None
        level = getattr(message, "level", message.type)
        return f"{message.exchange_segment}|{message.instrument_token}|{message.type}|{level}"

    def _handle_binary_frame(self, frame: bytes) -> None:
        """Split a binary batch into packets, decode each, and deliver.

        While a subscribe acknowledgement is outstanding (``_ack_pending``),
        decoded messages are **not delivered** immediately, *except* for
        messages this client already has a resolved ``trading_symbol`` for
        (see ``_pending_key``) and messages that are never withheld
        (``market_status`` events — see ``_pending_key``). Everything else is
        kept in ``_pending_latest_by_key``, one entry per (instrument, message
        type/level) — each new message for the same key overwrites the
        previous one, so at most one (the freshest) tick per key is ever
        held. This is a live price feed: an out-of-date tick is worthless
        once a newer one for the same key has arrived, so there is no value
        in queuing a backlog.

        As soon as the ack lands (in ``_handle_text_frame``) or
        ``ack_wait_timeout`` passes without one, every held-back key's
        latest message is delivered — enriched with its now-known
        ``trading_symbol`` — and delivery reverts to normal, per-message
        handling for anything that arrives afterward.
        """
        for packet in split_batch(frame):
            message = self._decode_packet(packet)
            if message is None:
                continue
            if self._ack_pending and self._trading_symbol_for(message) is None:
                if self._ack_deadline_passed():
                    # Backstop: forcibly end the window regardless of how
                    # many acks are still outstanding. Normally
                    # _wait_for_subscribe_ack's own timeout (fix for the
                    # quiet-feed case) gets there first; this only matters
                    # if a future frame's deadline check fires before that
                    # wait resolves.
                    self._ack_pending = False
                    self._ack_deadline = None
                    self._acks_outstanding = 0
                    self._flush_pending_latest_messages()
                else:
                    key = self._pending_key(message)
                    if key is not None:
                        self._pending_latest_by_key[key] = message
                        continue
            self._deliver_message(message)

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
        ``trading_symbol=None`` before the map is ready. Each call increments
        ``_acks_outstanding``; the withholding window only ends once every
        subscribe sent so far has been resolved (ack received, or timed out
        via ``_wait_for_subscribe_ack``) — see ``_handle_text_frame`` and
        ``_wait_for_subscribe_ack``.
        """
        self._subscribe_ack_event.clear()
        self._acks_outstanding += 1
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

        If the wait times out, releases this subscribe's share of the
        withholding window immediately (see ``_acks_outstanding``) instead
        of relying on ``_handle_binary_frame``'s deadline check, which only
        runs when a *future* frame happens to arrive. On a quiet/thinly
        traded instrument, no such frame may ever come, and anything parked
        so far would otherwise be withheld forever. The deadline check in
        ``_handle_binary_frame`` stays in place as a second line of
        defence for paths that don't wait here (e.g. ``snapshot()`` calling
        this same method covers itself, but a raw ``_send_subscribe``
        caller that skips this method entirely would not).
        """
        if self._receive_task is None:
            return
        try:
            await asyncio.wait_for(self._subscribe_ack_event.wait(), timeout=self.ack_wait_timeout)
        except asyncio.TimeoutError:
            self._acks_outstanding = max(0, self._acks_outstanding - 1)
            if self._acks_outstanding == 0:
                self._ack_pending = False
                self._ack_deadline = None
                self._flush_pending_latest_messages()

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

        # _send_subscribe (reused here for its ack_symbol plumbing) arms the
        # withholding window the same way a real subscribe does. Unlike
        # subscribe_scrips() etc., snapshot() has no separate bookkeeping
        # step to run first, so wait for the ack right away -- otherwise
        # the live feed would stay paused behind this snapshot until some
        # unrelated future frame happens to trip the deadline check.
        await self._wait_for_subscribe_ack()

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
