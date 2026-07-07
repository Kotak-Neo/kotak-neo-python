"""Async/await WebSocket client for the Order & Position streaming API.

Streams real-time order-lifecycle events (new, validation, open, complete,
rejected, ...) and live position updates over ``wss://<baseurl>/realtime``,
where ``<baseurl>`` is the host returned by ``/tradeApiValidate`` (stored on the
configuration as ``base_url``).

The connection handshake is a **raw (non-JSON) string** sent immediately after
the socket opens::

    {type:cn,Authorization:<token>,Sid:<sid>,src:WEB}
"""

import asyncio
import contextlib
import json
import ssl
from collections.abc import AsyncIterator, Callable
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import websockets

from neo_api_client.websocket.orderfeed.exceptions import (
    AlreadyConnectedError,
    AuthenticationError,
    ConnectionError,
    NotConnectedError,
)
from neo_api_client.websocket.orderfeed.models import OrderUpdate, PositionUpdate


def _to_realtime_url(base_url: str) -> str:
    """Derive the ``wss://<host>/realtime`` endpoint from an http(s) base URL.

    ``tradeApiValidate`` returns a base URL like ``https://e21.kotaksecurities.com``;
    the order feed lives at ``wss://e21.kotaksecurities.com/realtime``.
    """
    parts = urlsplit(base_url)
    scheme = "wss" if parts.scheme in ("https", "wss", "") else "ws"
    # Support base URLs given with or without a scheme/host split.
    netloc = parts.netloc or parts.path
    path = "/realtime"
    return urlunsplit((scheme, netloc, path, "", ""))


class OrderFeedWebSocket:
    """Async/await client for the Order & Position streaming feed.

    Example:
        ```python
        async with client.create_order_feed() as ws:
            async for message in ws:
                print(message)
        ```
    """

    def __init__(
        self,
        base_url: str,
        auth: str,
        sid: str,
        *,
        source: str = "WEB",
        reconnect_delay: int = 5,
        max_reconnect_attempts: int = 5,
        ping_interval: int = 20,
    ):
        """Initialize the client.

        Args:
            base_url: Base URL from ``/tradeApiValidate`` (e.g.
                ``https://e21.kotaksecurities.com``). Converted to
                ``wss://<host>/realtime``.
            auth: Session token (``edit_token`` from tradeApiValidate).
            sid: Session id (``edit_sid`` from tradeApiValidate).
            source: ``src`` value in the connection payload (default 'WEB').
            reconnect_delay: Seconds between reconnect attempts.
            max_reconnect_attempts: Maximum reconnect attempts.
            ping_interval: WebSocket-level ping interval (keep-alive), seconds.
        """
        self.base_url = base_url
        self.url = _to_realtime_url(base_url) if base_url else None
        self.auth = auth
        self.sid = sid
        self.source = source
        self.reconnect_delay = reconnect_delay
        self.max_reconnect_attempts = max_reconnect_attempts
        self.ping_interval = ping_interval

        self._ws: Any = None
        self._connected = False
        self._receive_task: asyncio.Task | None = None
        self._message_queue: asyncio.Queue = asyncio.Queue()
        self._reconnect_count = 0

        # Callbacks
        self.on_message: Callable[[Any], None] | None = None
        self.on_error: Callable[[Exception], None] | None = None
        self.on_connect: Callable[[], None] | None = None
        self.on_disconnect: Callable[[], None] | None = None
        # Raw-frame hook: every frame (str/bytes) before parsing (debugging).
        self.on_raw: Callable[[Any], None] | None = None

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    def __aiter__(self) -> AsyncIterator[Any]:
        return self

    async def __anext__(self) -> Any:
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

    def _build_auth_payload(self) -> str:
        """Build the raw (NON-JSON) connection string sent after open."""
        return f"{{type:cn,Authorization:{self.auth},Sid:{self.sid},src:{self.source}}}"

    async def connect(self) -> None:
        """Open the socket and send the connection payload.

        Raises:
            AlreadyConnectedError: If already connected.
            ConnectionError: If the socket fails to open or is misconfigured.
            AuthenticationError: If sending the connection payload fails.
        """
        if self.is_connected:
            raise AlreadyConnectedError("WebSocket is already connected")
        if not self.url:
            raise ConnectionError(
                "No base URL available. Complete totp_validate() first so the "
                "order-feed base URL is known."
            )

        try:
            ssl_context = None
            if self.url.startswith("wss"):
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE

            self._ws = await websockets.connect(
                self.url,
                ssl=ssl_context,
                ping_interval=self.ping_interval,
            )
            self._connected = True
        except Exception as e:
            self._connected = False
            raise ConnectionError(f"Failed to connect: {e}") from e

        # Send the mandatory raw connection payload immediately after open.
        try:
            await self._ws.send(self._build_auth_payload())
        except Exception as e:
            self._connected = False
            with contextlib.suppress(Exception):
                await self._ws.close()
            self._ws = None
            raise AuthenticationError(f"Failed to send connection payload: {e}") from e

        self._receive_task = asyncio.create_task(self._receive_loop())
        self._reconnect_count = 0
        if self.on_connect:
            self.on_connect()

    async def _receive_loop(self) -> None:
        """Receive frames, decode (JSON when possible), and enqueue."""
        while self.is_connected:
            try:
                raw = await self._ws.recv()

                if self.on_raw:
                    with contextlib.suppress(Exception):
                        self.on_raw(raw)

                message = self._parse_message(raw)
                if message is None:
                    continue
                self._message_queue.put_nowait(message)
                if self.on_message:
                    with contextlib.suppress(Exception):
                        self.on_message(message)

            except websockets.exceptions.ConnectionClosed:
                self._connected = False
                await self._handle_disconnect()
                break
            except Exception as e:  # pragma: no cover - defensive
                if self.on_error:
                    self.on_error(e)

    def _parse_message(self, raw: Any) -> Any:
        """Decode a frame into a typed message, or None to skip it.

        - ``order``    -> :class:`OrderUpdate`
        - ``position`` -> :class:`PositionUpdate`
        - ``cn`` (connection ack) -> None (control frame, not surfaced)
        - anything else / unparseable -> the raw dict or string as-is

        Never raises; a single malformed frame can't tear down the receive loop.
        """
        if isinstance(raw, (bytes, bytearray)):
            try:
                raw = raw.decode("utf-8")
            except Exception:
                return raw

        if isinstance(raw, str):
            try:
                data = json.loads(raw)
            except (json.JSONDecodeError, ValueError):
                return raw
        else:
            data = raw

        if not isinstance(data, dict):
            return data

        msg_type = data.get("type")
        try:
            if msg_type == "order":
                return OrderUpdate(**data)
            if msg_type == "position":
                return PositionUpdate(**data)
        except Exception as e:  # pragma: no cover - defensive
            # Fall back to the raw dict if the payload doesn't fit the model.
            if self.on_error:
                self.on_error(e)
            return data

        # Connection acknowledgement (type == "cn") is a control frame; the
        # handshake already consumed it, so drop any that arrive on the stream.
        if data.get("ak") == "ok" or msg_type == "cn":
            return None

        # Unknown message type: surface the raw dict rather than dropping it.
        return data

    async def _handle_disconnect(self) -> None:
        """Reconnect from scratch (server pushes state again on reconnect)."""
        self._connected = False
        if self.on_disconnect:
            self.on_disconnect()

        if self._reconnect_count >= self.max_reconnect_attempts:
            return
        self._reconnect_count += 1
        await asyncio.sleep(self.reconnect_delay)

        try:
            await self.connect()
        except Exception as e:
            if self.on_error:
                self.on_error(e)
            await self._handle_disconnect()

    async def close(self) -> None:
        """Close the socket and clean up."""
        self._connected = False

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
