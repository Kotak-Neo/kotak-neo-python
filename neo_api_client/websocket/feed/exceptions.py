"""Exceptions for SFeed WebSocket client."""


class SFeedWebSocketError(Exception):
    """Base exception for SFeed WebSocket errors."""

    pass


class ConnectionError(SFeedWebSocketError):
    """Raised when WebSocket connection fails."""

    pass


class AuthenticationError(SFeedWebSocketError):
    """Raised when authentication fails."""

    pass


class SubscriptionError(SFeedWebSocketError):
    """Raised when subscription request fails."""

    pass


class MessageParseError(SFeedWebSocketError):
    """Raised when unable to parse incoming message."""

    pass


class AlreadyConnectedError(SFeedWebSocketError):
    """Raised when attempting to connect while already connected."""

    pass


class NotConnectedError(SFeedWebSocketError):
    """Raised when attempting to use WebSocket before connection."""

    pass
