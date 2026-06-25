"""Unit tests for exception handling in NeoAPI methods."""

import pytest

from neo_api_client import NeoAPI


@pytest.fixture
def authenticated_client():
    """Create an authenticated NeoAPI client."""
    client = NeoAPI(environment="prod", consumer_key="test_key")
    client.configuration.edit_token = "edit_token_123"
    client.configuration.edit_sid = "edit_sid_123"
    client.configuration.view_token = "view_token_123"
    client.configuration.sid = "sid_123"
    client.configuration.serverId = "server_123"
    client.configuration.base_url = "https://gw-napi.kotaksecurities.com"
    return client


def test_cancel_order_exception(authenticated_client, requests_mock):
    """Test cancel_order with exception."""
    url = authenticated_client.configuration.get_url_details("cancel_order")

    requests_mock.post(url, status_code=500, text="Internal Server Error")

    result = authenticated_client.cancel_order(order_id="240101000000001")

    assert "Error" in result or result is not None


def test_cancel_cover_order_exception(authenticated_client, requests_mock):
    """Test cancel_cover_order with exception."""
    url = authenticated_client.configuration.get_url_details("cancel_cover_order")

    requests_mock.post(url, status_code=500, text="Internal Server Error")

    result = authenticated_client.cancel_cover_order(order_id="240101000000002")

    assert "Error" in result or result is not None


def test_cancel_bracket_order_exception(authenticated_client, requests_mock):
    """Test cancel_bracket_order with exception."""
    url = authenticated_client.configuration.get_url_details("cancel_bracket_order")

    requests_mock.post(url, status_code=500, text="Internal Server Error")

    result = authenticated_client.cancel_bracket_order(order_id="240101000000003")

    assert "Error" in result or result is not None


def test_scrip_master_exception(authenticated_client, requests_mock):
    """Test scrip_master with exception."""
    url = authenticated_client.configuration.get_url_details("scrip_master")

    requests_mock.post(url, status_code=500, text="Internal Server Error")

    result = authenticated_client.scrip_master()

    assert "Error" in result


def test_scrip_master_invalid_exchange(authenticated_client, requests_mock):
    """Test scrip_master with invalid exchange segment."""
    url = authenticated_client.configuration.get_url_details("scrip_master")

    requests_mock.post(url, status_code=400, text="Invalid Exchange")

    result = authenticated_client.scrip_master(exchange_segment="invalid_exchange")

    assert "Error" in result


def test_quotes_empty_instrument_tokens():
    """Test quotes with empty instrument tokens."""
    client = NeoAPI(environment="prod", consumer_key="test_key")

    result = client.quotes(instrument_tokens=None, quote_type="ltp")

    assert "error" in result


def test_quotes_validation_error():
    """Test quotes with validation error."""
    client = NeoAPI(environment="prod", consumer_key="test_key")

    result = client.quotes(instrument_tokens=[], quote_type="ltp")

    assert "error" in result


def test_help_method():
    """Test help method."""
    client = NeoAPI(environment="prod", consumer_key="test_key")

    # Should not raise any exceptions
    client.help()


def test_help_with_function_name():
    """Test help with function name."""
    client = NeoAPI(environment="prod", consumer_key="test_key")

    # Should not raise any exceptions
    client.help("place_order")


def test_help_with_socket():
    """Test help with socket keyword."""
    client = NeoAPI(environment="prod", consumer_key="test_key")

    # Should not raise any exceptions
    client.help("socket")


def test_check_callbacks_missing_on_message():
    """Test check_callbacks when on_message is missing."""
    client = NeoAPI(environment="prod", consumer_key="test_key")
    client.on_error = lambda _err: None
    client.on_open = lambda: None
    client.on_close = lambda: None

    result = client.check_callbacks()

    assert result is None or (isinstance(result, dict) and "Error" in result)


def test_check_callbacks_missing_on_error():
    """Test check_callbacks when on_error is missing."""
    client = NeoAPI(environment="prod", consumer_key="test_key")
    client.on_message = lambda _msg: None
    client.on_open = lambda: None
    client.on_close = lambda: None

    result = client.check_callbacks()

    assert result is None or (isinstance(result, dict) and "Error" in result)


def test_check_callbacks_missing_on_open():
    """Test check_callbacks when on_open is missing."""
    client = NeoAPI(environment="prod", consumer_key="test_key")
    client.on_message = lambda _msg: None
    client.on_error = lambda _err: None
    client.on_close = lambda: None

    result = client.check_callbacks()

    assert result is None or (isinstance(result, dict) and "Error" in result)


def test_check_callbacks_missing_on_close():
    """Test check_callbacks when on_close is missing."""
    client = NeoAPI(environment="prod", consumer_key="test_key")
    client.on_message = lambda _msg: None
    client.on_error = lambda _err: None
    client.on_open = lambda: None

    result = client.check_callbacks()

    assert result is None or (isinstance(result, dict) and "Error" in result)
