"""
Custom Exceptions can be created in this file

Enhanced exception hierarchy with better context and categorization.
Provides enterprise-grade error handling with detailed context,
categorization, and actionable information for error recovery.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any


class OpenApiException(Exception):
    """The base exception class for all OpenAPIExceptions"""


class ApiTypeError(OpenApiException, TypeError):
    def __init__(self, msg, path_to_item=None, valid_classes=None, key_type=None):
        """Raises an exception for TypeErrors
        Args:
            msg (str): the exception message
        Keyword Args:
            path_to_item (list): a list of keys an indices to get to the
                                 current_item
                                 None if unset
            valid_classes (tuple): the primitive classes that current item
                                   should be an instance of
                                   None if unset
            key_type (bool): False if our value is a value in a dict
                             True if it is a key in a dict
                             False if our item is an item in a list
                             None if unset
        """
        self.path_to_item = path_to_item
        self.valid_classes = valid_classes
        self.key_type = key_type
        full_msg = msg
        if path_to_item:
            full_msg = f"{msg} at {render_path(path_to_item)}"
        super().__init__(full_msg)


class ApiValueError(OpenApiException, ValueError):
    def __init__(self, msg, path_to_item=None):
        """
        Args:
            msg (str): the exception message
        Keyword Args:
            path_to_item (list) the path to the exception in the
                received_data dict. None if unset
        """

        self.path_to_item = path_to_item
        full_msg = msg
        if path_to_item:
            full_msg = f"{msg} at {render_path(path_to_item)}"
        super().__init__(full_msg)


class ApiAttributeError(OpenApiException, AttributeError):
    def __init__(self, msg, path_to_item=None):
        """
        Raised when an attribute reference or assignment fails.
        Args:
            msg (str): the exception message
        Keyword Args:
            path_to_item (None/list) the path to the exception in the
                received_data dict
        """
        self.path_to_item = path_to_item
        full_msg = msg
        if path_to_item:
            full_msg = f"{msg} at {render_path(path_to_item)}"
        super().__init__(full_msg)


class ApiKeyError(OpenApiException, KeyError):
    def __init__(self, msg, path_to_item=None):
        """
        Args:
            msg (str): the exception message
        Keyword Args:
            path_to_item (None/list) the path to the exception in the
                received_data dict
        """
        self.path_to_item = path_to_item
        full_msg = msg
        if path_to_item:
            full_msg = f"{msg} at {render_path(path_to_item)}"
        super().__init__(full_msg)


class ApiException(OpenApiException):
    def __init__(self, status=None, reason=None, http_resp=None, body=None):
        if http_resp:
            self.status = http_resp.status
            self.reason = http_resp.reason
            self.body = http_resp.data
            self.headers = http_resp.getheaders()
            self.error_message = None
        else:
            self.status = status
            self.reason = reason
            self.body = None
            self.headers = None
        if body:
            self.body = body
        if status:
            self.status = status
        if reason:
            self.reason = reason
        self.__str__()
        super().__init__(self.error_message)

    def __str__(self):
        """Custom error messages for exception"""
        error_message = f"({self.status})\nReason: {self.reason}\n"
        if self.headers:
            error_message += f"HTTP response headers: {self.headers}\n"

        if self.body:
            error_message += f"HTTP response body: {self.body}\n"
        self.error_message = error_message
        return self.error_message


def render_path(path_to_item):
    """Returns a string representation of a path"""
    result = ""
    for pth in path_to_item:
        if isinstance(pth, int):
            result += f"[{pth}]"
        else:
            result += f"['{pth}']"
    return result


# Enhanced exception classes below


class ErrorCategory(Enum):
    """Categorize errors for better handling and monitoring."""

    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    VALIDATION = "validation"
    RATE_LIMIT = "rate_limit"
    SERVER_ERROR = "server_error"
    NETWORK = "network"
    TIMEOUT = "timeout"
    CONFIGURATION = "configuration"
    UNKNOWN = "unknown"


class ErrorSeverity(Enum):
    """Error severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NeoAPIException(Exception):
    """
    Base exception for Neo API with enhanced context.

    Attributes:
        message: Human-readable error message
        category: Error category for handling logic
        severity: Error severity level
        status_code: HTTP status code (if applicable)
        response_body: Raw response body
        request_id: Request correlation ID for tracing
        retryable: Whether the error is transient and retryable
        original_exception: The original exception (if wrapped)
        timestamp: When the error occurred
        context: Additional context about the error
    """

    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        status_code: int | None = None,
        response_body: Any | None = None,
        request_id: str | None = None,
        retryable: bool = False,
        original_exception: Exception | None = None,
        **context,
    ):
        """
        Initialize enhanced exception.

        Args:
            message: Error message
            category: Error category
            severity: Error severity
            status_code: HTTP status code
            response_body: API response body
            request_id: Request ID for tracing
            retryable: Whether error is retryable
            original_exception: Original exception if wrapping
            **context: Additional context key-value pairs
        """
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.status_code = status_code
        self.response_body = response_body
        self.request_id = request_id
        self.retryable = retryable
        self.original_exception = original_exception
        self.timestamp = datetime.now(timezone.utc)
        self.context = context

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize exception for logging and monitoring.

        Returns:
            Dictionary representation of the exception
        """
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "category": self.category.value,
            "severity": self.severity.value,
            "status_code": self.status_code,
            "request_id": self.request_id,
            "retryable": self.retryable,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context,
        }

    def __str__(self) -> str:
        """String representation."""
        parts = [f"{self.__class__.__name__}: {self.message}"]
        if self.request_id:
            parts.append(f"[Request ID: {self.request_id}]")
        if self.status_code:
            parts.append(f"[Status: {self.status_code}]")
        return " ".join(parts)


class AuthenticationError(NeoAPIException):
    """
    Authentication failed.

    Raised when credentials are invalid or authentication fails.
    """

    def __init__(self, message: str = "Authentication failed", **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.HIGH,
            retryable=False,
            **kwargs,
        )


class AuthorizationError(NeoAPIException):
    """
    Authorization failed.

    Raised when user doesn't have permission for the requested operation.
    """

    def __init__(self, message: str = "Authorization failed", **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.AUTHORIZATION,
            severity=ErrorSeverity.MEDIUM,
            retryable=False,
            **kwargs,
        )


class ValidationError(NeoAPIException):
    """
    Request validation failed.

    Raised when input parameters don't meet requirements.
    """

    def __init__(self, message: str = "Validation failed", field: str | None = None, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.MEDIUM,
            retryable=False,
            field=field,
            **kwargs,
        )
        self.field = field


class RateLimitError(NeoAPIException):
    """
    Rate limit exceeded.

    Raised when API rate limits are exceeded.
    """

    def __init__(
        self, message: str = "Rate limit exceeded", retry_after: int | None = None, **kwargs
    ):
        # Default to 429 but allow callers (e.g. map_http_status_to_exception)
        # to pass status_code explicitly without conflicting.
        kwargs.setdefault("status_code", 429)
        super().__init__(
            message=message,
            category=ErrorCategory.RATE_LIMIT,
            severity=ErrorSeverity.MEDIUM,
            retryable=True,
            retry_after=retry_after,
            **kwargs,
        )
        self.retry_after = retry_after


class NetworkError(NeoAPIException):
    """
    Network connectivity error.

    Raised when network connection fails.
    """

    def __init__(self, message: str = "Network error occurred", **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.HIGH,
            retryable=True,
            **kwargs,
        )


class TimeoutError(NeoAPIException):
    """
    Request timeout.

    Raised when request exceeds timeout limit.
    """

    def __init__(
        self, message: str = "Request timeout", timeout_seconds: float | None = None, **kwargs
    ):
        super().__init__(
            message=message,
            category=ErrorCategory.TIMEOUT,
            severity=ErrorSeverity.MEDIUM,
            retryable=True,
            timeout_seconds=timeout_seconds,
            **kwargs,
        )
        self.timeout_seconds = timeout_seconds


class ServerError(NeoAPIException):
    """
    Server-side error.

    Raised when API server returns 5xx error.
    """

    def __init__(self, message: str = "Server error occurred", **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.SERVER_ERROR,
            severity=ErrorSeverity.HIGH,
            retryable=True,
            **kwargs,
        )


class ConfigurationError(NeoAPIException):
    """
    SDK configuration error.

    Raised when SDK is misconfigured.
    """

    def __init__(self, message: str = "Configuration error", **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.CONFIGURATION,
            severity=ErrorSeverity.CRITICAL,
            retryable=False,
            **kwargs,
        )


class OrderError(NeoAPIException):
    """
    Order-related error.

    Raised when order operations fail.
    """

    def __init__(
        self, message: str = "Order operation failed", order_id: str | None = None, **kwargs
    ):
        super().__init__(message=message, severity=ErrorSeverity.HIGH, order_id=order_id, **kwargs)
        self.order_id = order_id


class WebSocketError(NeoAPIException):
    """
    WebSocket connection error.

    Raised when WebSocket operations fail.
    """

    def __init__(self, message: str = "WebSocket error", **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM,
            retryable=True,
            **kwargs,
        )


def map_http_status_to_exception(
    status_code: int, message: str | None = None, **kwargs
) -> NeoAPIException:
    """
    Map HTTP status code to appropriate exception.

    Args:
        status_code: HTTP status code
        message: Optional custom message
        **kwargs: Additional context

    Returns:
        Appropriate exception instance
    """
    if status_code == 401:
        return AuthenticationError(
            message=message or "Authentication required", status_code=status_code, **kwargs
        )
    elif status_code == 403:
        return AuthorizationError(
            message=message or "Access forbidden", status_code=status_code, **kwargs
        )
    elif status_code == 400 or status_code == 422:
        return ValidationError(
            message=message or "Invalid request", status_code=status_code, **kwargs
        )
    elif status_code == 429:
        return RateLimitError(
            message=message or "Too many requests", status_code=status_code, **kwargs
        )
    elif status_code == 408:
        return TimeoutError(message=message or "Request timeout", status_code=status_code, **kwargs)
    elif 500 <= status_code < 600:
        return ServerError(
            message=message or f"Server error ({status_code})", status_code=status_code, **kwargs
        )
    else:
        return NeoAPIException(
            message=message or f"API error ({status_code})", status_code=status_code, **kwargs
        )
