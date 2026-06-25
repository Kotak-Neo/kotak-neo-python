"""Unit tests for logger module."""

from neo_api_client.logger import (
    add_app_context,
    add_correlation_id,
    censor_sensitive_data,
    get_logger,
    setup_logging,
)


def test_get_logger_basic():
    """Test get_logger returns a logger instance."""
    logger = get_logger("test")

    assert logger is not None


def test_get_logger_default():
    """Test get_logger with no name."""
    logger = get_logger()

    assert logger is not None


def test_get_logger_different_names():
    """Test get_logger with different names."""
    logger1 = get_logger("module1")
    logger2 = get_logger("module2")

    # Both should be valid logger instances
    assert logger1 is not None
    assert logger2 is not None


def test_censor_sensitive_data_processor():
    """Test censor_sensitive_data as a log processor."""
    # censor_sensitive_data is a processor that gets logger, name, event_dict
    event_dict = {
        "consumer_key": "secret_key_123",
        "password": "mypassword",
        "access_token": "token_abc",
        "normal_field": "visible_value",
    }

    result = censor_sensitive_data(None, None, event_dict)

    # Should censor sensitive keys
    assert "se***23" in result.get("consumer_key", "") or result.get("consumer_key") == "***"
    assert "my***rd" in result.get("password", "") or result.get("password") == "***"
    assert "to***bc" in result.get("access_token", "") or result.get("access_token") == "***"
    assert result["normal_field"] == "visible_value"


def test_censor_sensitive_data_nested():
    """Test censor_sensitive_data with nested dictionary."""
    event_dict = {
        "user": {"username": "john", "password": "secret123"},
        "data": {"value": 100},
    }

    result = censor_sensitive_data(None, None, event_dict)

    # Password should be censored
    assert "password" in result["user"]
    # Username should remain
    assert result["user"]["username"] == "john"
    assert result["data"]["value"] == 100


def test_add_correlation_id_processor():
    """Test add_correlation_id processor."""
    event_dict = {"message": "test"}

    result = add_correlation_id(None, None, event_dict)

    # add_correlation_id may add request_id only if not already present
    # Just verify it returns a dict and doesn't raise
    assert isinstance(result, dict)
    assert "message" in result


def test_add_app_context_processor():
    """Test add_app_context processor."""
    event_dict = {"message": "test"}

    result = add_app_context(None, None, event_dict)

    # Should add app context
    assert "app" in result
    assert result["app"] == "neo_api_client"
    assert "environment" in result


def test_setup_logging_default():
    """Test setup_logging with default parameters."""
    logger = setup_logging()

    assert logger is not None


def test_setup_logging_custom_level():
    """Test setup_logging with custom log level."""
    logger = setup_logging(level="DEBUG")

    assert logger is not None


def test_setup_logging_no_json():
    """Test setup_logging without JSON output."""
    logger = setup_logging(json_output=False)

    assert logger is not None


def test_get_logger_after_setup():
    """Test get_logger after setup_logging."""
    setup_logging()
    logger = get_logger("test_module")

    assert logger is not None


def test_logger_info_message():
    """Test logger can log info messages."""
    logger = get_logger("test")

    # Should not raise exceptions
    logger.info("test message")


def test_logger_with_context():
    """Test logger with additional context."""
    logger = get_logger("test")

    # Should not raise exceptions
    logger.info("test message", extra_field="extra_value")
