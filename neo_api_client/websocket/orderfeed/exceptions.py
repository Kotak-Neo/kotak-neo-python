"""Exceptions for the Order & Position streaming WebSocket client."""


class OrderFeedWebSocketError(Exception):
    """Base exception for Order Feed WebSocket errors."""

    pass


class ConnectionError(OrderFeedWebSocketError):
    """Raised when the WebSocket connection fails."""

    pass


class AuthenticationError(OrderFeedWebSocketError):
    """Raised when authentication fails."""

    pass


class AlreadyConnectedError(OrderFeedWebSocketError):
    """Raised when attempting to connect while already connected."""

    pass


class NotConnectedError(OrderFeedWebSocketError):
    """Raised when using the socket before it is connected."""

    pass
