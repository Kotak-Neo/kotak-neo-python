from neo_api_client.exceptions import (
    ApiAttributeError,
    ApiException,
    ApiKeyError,
    ApiTypeError,
    ApiValueError,
    AuthenticationError,
    ConfigurationError,
    ErrorCategory,
    ErrorSeverity,
    NeoAPIException,
    NetworkError,
    OpenApiException,
    RateLimitError,
    ValidationError,
    render_path,
)


def test_api_exception():
    exc = ApiException(
        status=400,
        reason="Bad Request",
    )

    assert exc.status == 400
    assert exc.reason == "Bad Request"


def test_api_exception_with_body():
    """Test ApiException with body parameter"""
    exc = ApiException(
        status=500,
        reason="Internal Server Error",
        body='{"error": "Something went wrong"}',
    )

    assert exc.status == 500
    assert exc.reason == "Internal Server Error"
    assert exc.body == '{"error": "Something went wrong"}'


def test_api_exception_with_http_resp():
    """Test ApiException with http_resp parameter"""

    class MockHttpResp:
        status = 404
        reason = "Not Found"
        data = b"Page not found"

        def getheaders(self):
            return [("Content-Type", "text/html")]

    mock_resp = MockHttpResp()
    exc = ApiException(http_resp=mock_resp)

    assert exc.status == 404
    assert exc.reason == "Not Found"
    assert exc.body == b"Page not found"
    assert exc.headers == [("Content-Type", "text/html")]


def test_api_exception_str():
    """Test ApiException string representation"""
    exc = ApiException(status=403, reason="Forbidden")
    assert exc.error_message is not None
    assert "403" in exc.error_message
    assert "Forbidden" in exc.error_message


def test_open_api_exception():
    """Test base OpenApiException class"""
    exc = OpenApiException("Test exception")
    assert str(exc) == "Test exception"


def test_api_type_error_basic():
    """Test ApiTypeError with basic parameters"""
    exc = ApiTypeError(msg="Invalid type")
    assert str(exc) == "Invalid type"


def test_api_type_error_with_path():
    """Test ApiTypeError with path_to_item"""
    exc = ApiTypeError(
        msg="Type error",
        path_to_item=["data", 0, "price"],
        valid_classes=(int, float),
        key_type=False,
    )
    assert "Type error" in str(exc)
    assert "['data'][0]['price']" in str(exc)
    assert exc.path_to_item == ["data", 0, "price"]
    assert exc.valid_classes == (int, float)
    assert exc.key_type is False


def test_api_type_error_with_int_path():
    """Test ApiTypeError with integer in path"""
    exc = ApiTypeError(msg="Invalid type", path_to_item=[0, 1, 2])
    assert "[0][1][2]" in str(exc)


def test_api_value_error_basic():
    """Test ApiValueError with basic parameters"""
    exc = ApiValueError(msg="Invalid value")
    assert str(exc) == "Invalid value"


def test_api_value_error_with_path():
    """Test ApiValueError with path_to_item"""
    exc = ApiValueError(msg="Value out of range", path_to_item=["config", "timeout"])
    assert "Value out of range" in str(exc)
    assert "['config']['timeout']" in str(exc)
    assert exc.path_to_item == ["config", "timeout"]


def test_api_attribute_error_basic():
    """Test ApiAttributeError with basic parameters"""
    exc = ApiAttributeError(msg="Attribute not found")
    assert str(exc) == "Attribute not found"


def test_api_attribute_error_with_path():
    """Test ApiAttributeError with path_to_item"""
    exc = ApiAttributeError(msg="Missing attribute", path_to_item=["user", "email"])
    assert "Missing attribute" in str(exc)
    assert "['user']['email']" in str(exc)
    assert exc.path_to_item == ["user", "email"]


def test_api_key_error_basic():
    """Test ApiKeyError with basic parameters"""
    exc = ApiKeyError(msg="Key not found")
    assert "Key not found" in str(exc)


def test_api_key_error_with_path():
    """Test ApiKeyError with path_to_item"""
    exc = ApiKeyError(msg="Missing key", path_to_item=["response", "data"])
    assert "Missing key" in str(exc)
    assert "['response']['data']" in str(exc)
    assert exc.path_to_item == ["response", "data"]


def test_render_path_string_keys():
    """Test render_path with string keys"""
    path = ["data", "orders", "first"]
    result = render_path(path)
    assert result == "['data']['orders']['first']"


def test_render_path_int_indices():
    """Test render_path with integer indices"""
    path = ["items", 0, "name"]
    result = render_path(path)
    assert result == "['items'][0]['name']"


def test_render_path_mixed():
    """Test render_path with mixed keys and indices"""
    path = ["response", 0, "data", 1, "value"]
    result = render_path(path)
    assert result == "['response'][0]['data'][1]['value']"


def test_render_path_empty():
    """Test render_path with empty path"""
    path = []
    result = render_path(path)
    assert result == ""


def test_api_type_error_none_optionals():
    """Test ApiTypeError with None optional parameters"""
    exc = ApiTypeError(
        msg="Type mismatch",
        path_to_item=None,
        valid_classes=None,
        key_type=None,
    )
    assert str(exc) == "Type mismatch"
    assert exc.path_to_item is None
    assert exc.valid_classes is None
    assert exc.key_type is None


def test_exception_inheritance():
    """Test that custom exceptions inherit from correct base classes"""
    assert issubclass(OpenApiException, Exception)
    assert issubclass(ApiTypeError, OpenApiException)
    assert issubclass(ApiTypeError, TypeError)
    assert issubclass(ApiValueError, OpenApiException)
    assert issubclass(ApiValueError, ValueError)
    assert issubclass(ApiAttributeError, OpenApiException)
    assert issubclass(ApiAttributeError, AttributeError)
    assert issubclass(ApiKeyError, OpenApiException)
    assert issubclass(ApiKeyError, KeyError)
    assert issubclass(ApiException, OpenApiException)


def test_error_category_enum():
    """Test ErrorCategory enum values."""
    assert ErrorCategory.AUTHENTICATION.value == "authentication"
    assert ErrorCategory.AUTHORIZATION.value == "authorization"
    assert ErrorCategory.VALIDATION.value == "validation"
    assert ErrorCategory.NETWORK.value == "network"
    assert ErrorCategory.RATE_LIMIT.value == "rate_limit"
    assert ErrorCategory.SERVER_ERROR.value == "server_error"
    assert ErrorCategory.TIMEOUT.value == "timeout"
    assert ErrorCategory.CONFIGURATION.value == "configuration"
    assert ErrorCategory.UNKNOWN.value == "unknown"


def test_error_severity_enum():
    """Test ErrorSeverity enum values."""
    assert ErrorSeverity.LOW.value == "low"
    assert ErrorSeverity.MEDIUM.value == "medium"
    assert ErrorSeverity.HIGH.value == "high"
    assert ErrorSeverity.CRITICAL.value == "critical"


def test_neo_api_exception_basic():
    """Test NeoAPIException with basic parameters."""
    exc = NeoAPIException(
        message="Test error",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.MEDIUM,
        retryable=False,
    )

    assert exc.message == "Test error"
    assert exc.category == ErrorCategory.VALIDATION
    assert exc.severity == ErrorSeverity.MEDIUM
    assert exc.retryable is False
    assert exc.timestamp is not None


def test_neo_api_exception_with_details():
    """Test NeoAPIException with detailed parameters."""
    exc = NeoAPIException(
        message="API call failed",
        category=ErrorCategory.NETWORK,
        severity=ErrorSeverity.HIGH,
        status_code=503,
        request_id="req_123",
        retryable=True,
        endpoint="/api/orders",
    )

    assert exc.status_code == 503
    assert exc.request_id == "req_123"
    assert exc.retryable is True
    assert exc.context["endpoint"] == "/api/orders"


def test_neo_api_exception_to_dict():
    """Test NeoAPIException serialization."""
    exc = NeoAPIException(
        message="Test error",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.MEDIUM,
        status_code=400,
        request_id="req_123",
    )

    result = exc.to_dict()

    assert result["error_type"] == "NeoAPIException"
    assert result["message"] == "Test error"
    assert result["category"] == "validation"
    assert result["severity"] == "medium"
    assert result["status_code"] == 400
    assert result["request_id"] == "req_123"
    assert "timestamp" in result


def test_neo_api_exception_str():
    """Test NeoAPIException string representation."""
    exc = NeoAPIException(
        message="Test error",
        category=ErrorCategory.SERVER_ERROR,
        severity=ErrorSeverity.HIGH,
        status_code=500,
        request_id="req_456",
    )

    result = str(exc)

    assert "NeoAPIException" in result
    assert "Test error" in result
    assert "req_456" in result
    assert "500" in result


def test_authentication_error():
    """Test AuthenticationError."""
    exc = AuthenticationError("Invalid credentials")

    assert exc.message == "Invalid credentials"
    assert exc.category == ErrorCategory.AUTHENTICATION
    assert exc.severity == ErrorSeverity.HIGH
    assert exc.retryable is False


def test_authentication_error_default():
    """Test AuthenticationError with default message."""
    exc = AuthenticationError()

    assert exc.message == "Authentication failed"
    assert exc.category == ErrorCategory.AUTHENTICATION


def test_validation_error():
    """Test ValidationError."""
    exc = ValidationError("Invalid price", field="price")

    assert exc.message == "Invalid price"
    assert exc.category == ErrorCategory.VALIDATION
    assert exc.severity == ErrorSeverity.MEDIUM
    assert exc.retryable is False
    assert exc.context["field"] == "price"


def test_validation_error_default():
    """Test ValidationError with default message."""
    exc = ValidationError()

    assert exc.message == "Validation failed"


def test_network_error():
    """Test NetworkError."""
    exc = NetworkError("Connection timeout")

    assert exc.message == "Connection timeout"
    assert exc.category == ErrorCategory.NETWORK
    assert exc.severity == ErrorSeverity.HIGH
    assert exc.retryable is True


def test_network_error_default():
    """Test NetworkError with default message."""
    exc = NetworkError()

    assert exc.message == "Network error occurred"


def test_rate_limit_error():
    """Test RateLimitError."""
    exc = RateLimitError(retry_after=60)

    assert exc.message == "Rate limit exceeded"
    assert exc.category == ErrorCategory.RATE_LIMIT
    assert exc.severity == ErrorSeverity.MEDIUM
    assert exc.retryable is True
    assert exc.context["retry_after"] == 60


def test_rate_limit_error_with_message():
    """Test RateLimitError with custom message."""
    exc = RateLimitError("Too many requests", retry_after=120)

    assert exc.message == "Too many requests"
    assert exc.context["retry_after"] == 120


def test_configuration_error():
    """Test ConfigurationError."""
    exc = ConfigurationError("Missing API key")

    assert exc.message == "Missing API key"
    assert exc.category == ErrorCategory.CONFIGURATION
    assert exc.severity == ErrorSeverity.CRITICAL
    assert exc.retryable is False


def test_configuration_error_default():
    """Test ConfigurationError with default message."""
    exc = ConfigurationError()

    assert exc.message == "Configuration error"
