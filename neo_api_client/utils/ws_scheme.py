"""Shared http(s) -> ws(s) URL scheme normalization.

The dynamic config service hands back feed endpoints using the ``https``
scheme even though the endpoint is a WebSocket -- the handshake is an HTTP
Upgrade over the same TLS connection an ``https`` URL would use, so only the
URI scheme needs correcting, not the host/path. Used by both the SFeed and
order-feed WebSocket clients.
"""

from urllib.parse import urlsplit, urlunsplit

_SCHEME_TO_WEBSOCKET = {"https": "wss", "http": "ws"}


def to_websocket_scheme(url: str) -> str:
    """Map an ``http(s)`` URL to the equivalent ``ws(s)`` URL; other schemes pass through."""
    parts = urlsplit(url)
    scheme = _SCHEME_TO_WEBSOCKET.get(parts.scheme, parts.scheme)
    return urlunsplit((scheme, parts.netloc, parts.path, parts.query, parts.fragment))
