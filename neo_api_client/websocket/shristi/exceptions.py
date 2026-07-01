"""Exceptions for Shristi WebSocket client."""


class ShristiWebSocketError(Exception):
    """Base exception for Shristi WebSocket errors."""

    pass


class ConnectionError(ShristiWebSocketError):
    """Raised when WebSocket connection fails."""

    pass


class AuthenticationError(ShristiWebSocketError):
    """Raised when authentication fails."""

    pass


class SubscriptionError(ShristiWebSocketError):
    """Raised when subscription request fails."""

    pass


class MessageParseError(ShristiWebSocketError):
    """Raised when unable to parse incoming message."""

    pass


class AlreadyConnectedError(ShristiWebSocketError):
    """Raised when attempting to connect while already connected."""

    pass


class NotConnectedError(ShristiWebSocketError):
    """Raised when attempting to use WebSocket before connection."""

    pass
