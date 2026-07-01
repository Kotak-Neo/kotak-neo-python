"""Exceptions for Srishti WebSocket client."""


class SrishtiWebSocketError(Exception):
    """Base exception for Srishti WebSocket errors."""

    pass


class ConnectionError(SrishtiWebSocketError):
    """Raised when WebSocket connection fails."""

    pass


class AuthenticationError(SrishtiWebSocketError):
    """Raised when authentication fails."""

    pass


class SubscriptionError(SrishtiWebSocketError):
    """Raised when subscription request fails."""

    pass


class MessageParseError(SrishtiWebSocketError):
    """Raised when unable to parse incoming message."""

    pass


class AlreadyConnectedError(SrishtiWebSocketError):
    """Raised when attempting to connect while already connected."""

    pass


class NotConnectedError(SrishtiWebSocketError):
    """Raised when attempting to use WebSocket before connection."""

    pass
