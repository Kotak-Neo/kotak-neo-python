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

# Shristi WebSocket (modern async/await)
try:
    from neo_api_client.websocket.shristi import (  # noqa: F401
        DepthLevel,
        SFeedIndex,
        SFeedMarketStatus,
        SFeedScrip,
        SFeedScripLite,
        ShristiWebSocket,
        WsToken,
    )

    __all_shristi__ = [
        "ShristiWebSocket",
        "WsToken",
        "SFeedScrip",
        "SFeedScripLite",
        "SFeedIndex",
        "SFeedMarketStatus",
        "DepthLevel",
    ]
except ImportError:
    # websockets package not installed
    __all_shristi__ = []

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
] + __all_shristi__
