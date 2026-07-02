from neo_api_client.__version__ import __version__, __version_info__
from neo_api_client.exceptions import (
    ApiException,
    AuthenticationError,
    AuthorizationError,
    ConfigurationError,
    NeoAPIException,
    NetworkError,
    OrderError,
    RateLimitError,
    ServerError,
    TimeoutError,
    ValidationError,
    WebSocketError,
)
from neo_api_client.neo_api import NeoAPI
from neo_api_client.services.order_report import OrderReportAPI
from neo_api_client.utils.neo_utility import NeoUtility

# SFeed WebSocket (modern async/await)
try:
    from neo_api_client.websocket.feed import (  # noqa: F401
        DepthLevel,
        SFeedIndex,
        SFeedMarketStatus,
        SFeedScrip,
        SFeedScripLite,
        SFeedWebSocket,
        WsToken,
    )

    __all_feed__ = [
        "SFeedWebSocket",
        "WsToken",
        "SFeedScrip",
        "SFeedScripLite",
        "SFeedIndex",
        "SFeedMarketStatus",
        "DepthLevel",
    ]
except ImportError:
    # Defensive: `websockets`/`pydantic` are core deps, but keep the SDK importable
    # even if the WebSocket extras are somehow unavailable.
    __all_feed__ = []

__all__ = [
    "NeoAPI",
    "NeoUtility",
    "OrderReportAPI",
    "__version__",
    "__version_info__",
    # Exceptions
    "ApiException",
    "NeoAPIException",
    "AuthenticationError",
    "AuthorizationError",
    "ValidationError",
    "RateLimitError",
    "NetworkError",
    "TimeoutError",
    "ServerError",
    "ConfigurationError",
    "OrderError",
    "WebSocketError",
] + __all_feed__
