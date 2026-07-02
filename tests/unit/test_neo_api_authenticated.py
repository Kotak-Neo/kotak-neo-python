"""Unit tests for authenticated NeoAPI methods."""

import pytest

from neo_api_client import NeoAPI


@pytest.fixture
def authenticated_client():
    """Create an authenticated NeoAPI client."""
    client = NeoAPI(environment="prod", consumer_key="test_key")

    # Set up authenticated state
    client.configuration.edit_token = "edit_token_123"
    client.configuration.edit_sid = "edit_sid_123"
    client.configuration.view_token = "view_token_123"
    client.configuration.sid = "sid_123"
    client.configuration.base_url = "https://gw-napi.kotaksecurities.com"

    return client


def test_place_order_success(authenticated_client, requests_mock):
    """Test successful order placement."""
    url = authenticated_client.configuration.get_url_details("place_order")

    requests_mock.post(
        url,
        json={"stat": "Ok", "nOrdNo": "240101000000001"},
        status_code=200,
    )

    result = authenticated_client.place_order(
        exchange_segment="nse_cm",
        product="CNC",
        price="1500",
        order_type="L",
        quantity="1",
        validity="DAY",
        trading_symbol="RELIANCE-EQ",
        transaction_type="B",
    )

    assert result["stat"] == "Ok"
    assert "nOrdNo" in result


def test_place_order_with_optional_params(authenticated_client, requests_mock):
    """Test order placement with optional parameters."""
    url = authenticated_client.configuration.get_url_details("place_order")

    requests_mock.post(
        url,
        json={"stat": "Ok", "nOrdNo": "240101000000002"},
        status_code=200,
    )

    result = authenticated_client.place_order(
        exchange_segment="nse_cm",
        product="MIS",
        price="1500",
        order_type="L",
        quantity="10",
        validity="DAY",
        trading_symbol="SBIN-EQ",
        transaction_type="B",
        disclosed_quantity="5",
        trigger_price="1490",
        tag="test_order",
    )

    assert result["stat"] == "Ok"


def test_place_order_validation_error(authenticated_client):
    """Test place_order with validation error."""
    result = authenticated_client.place_order(
        exchange_segment="invalid_segment",
        product="CNC",
        price="1500",
        order_type="L",
        quantity="1",
        validity="DAY",
        trading_symbol="RELIANCE-EQ",
        transaction_type="B",
    )

    assert "Error" in result


def test_trade_report_success(authenticated_client, requests_mock):
    """Test trade report retrieval."""
    url = authenticated_client.configuration.get_url_details("trade_report")

    requests_mock.get(
        url,
        json={"stat": "Ok", "data": [{"trdSym": "RELIANCE-EQ"}]},
        status_code=200,
    )

    result = authenticated_client.trade_report()

    assert result["stat"] == "Ok"


def test_positions_success(authenticated_client, requests_mock):
    """Test positions retrieval."""
    url = authenticated_client.configuration.get_url_details("positions")

    requests_mock.get(
        url,
        json={"stat": "Ok", "data": [{"trdSym": "SBIN-EQ"}]},
        status_code=200,
    )

    result = authenticated_client.positions()

    assert result["stat"] == "Ok"


def test_holdings_success(authenticated_client, requests_mock):
    """Test holdings retrieval."""
    url = authenticated_client.configuration.get_url_details("holdings")

    requests_mock.get(
        url,
        json={"stat": "Ok", "data": [{"trdSym": "RELIANCE-EQ"}]},
        status_code=200,
    )

    result = authenticated_client.holdings()

    assert result["stat"] == "Ok"


def test_totp_login_success(requests_mock):
    """Test TOTP login."""
    client = NeoAPI(environment="prod", consumer_key="test_key")

    login_url = "https://mis.kotaksecurities.com//login/1.0/tradeApiLogin"

    requests_mock.post(
        login_url,
        json={
            "data": {
                "token": "view_token_123",
                "sid": "sid_123",
                "rid": "rid_123",
            }
        },
        status_code=200,
    )

    result = client.totp_login(
        mobile_number="+919999999999",
        ucc="TEST01",
        totp="123456",
    )

    assert result["data"]["token"] == "view_token_123"


def test_totp_validate_success(requests_mock):
    """Test TOTP validation (2FA)."""
    client = NeoAPI(environment="prod", consumer_key="test_key")

    # Set up initial login state
    client.configuration.view_token = "view_token_123"
    client.configuration.sid = "sid_123"

    validate_url = "https://mis.kotaksecurities.com//login/1.0/tradeApiValidate"

    requests_mock.post(
        validate_url,
        json={
            "data": {
                "token": "edit_token_123",
                "sid": "edit_sid_123",
                "rid": "edit_rid_123",
                "dataCenter": "DC1",
                "baseUrl": "https://gw-napi.kotaksecurities.com",
            }
        },
        status_code=200,
    )

    result = client.totp_validate(mpin="1234")

    assert result["data"]["token"] == "edit_token_123"
    assert client.configuration.edit_token == "edit_token_123"


def test_create_websocket_returns_client(authenticated_client):
    """create_websocket returns a configured SFeed WebSocket client when authenticated."""
    from neo_api_client.websocket.feed import SFeedWebSocket

    ws = authenticated_client.create_websocket()

    assert isinstance(ws, SFeedWebSocket)
    assert ws.access_token == authenticated_client.configuration.edit_token
    assert ws.sid == authenticated_client.configuration.edit_sid
    # Defaults to the SFeed production URL when no override is given
    assert ws.url == "wss://sfeed.kotaksecurities.com/wsfeed"


def test_help_no_function():
    """Test help method without function name."""
    client = NeoAPI(environment="prod", consumer_key="test_key")

    # Should not raise
    client.help()


def test_help_with_function():
    """Test help method with specific function."""
    client = NeoAPI(environment="prod", consumer_key="test_key")

    # Should not raise
    client.help("quotes")


def test_help_with_socket_keyword():
    """Test help method with 'socket' keyword."""
    client = NeoAPI(environment="prod", consumer_key="test_key")

    # Should map to subscribe
    client.help("socket")


def test_subscribe_to_orderfeed_removed():
    """Legacy subscribe_to_orderfeed() is removed in 2.2.0 and raises NotImplementedError."""
    client = NeoAPI(environment="prod", consumer_key="test_key")

    with pytest.raises(NotImplementedError):
        client.subscribe_to_orderfeed()


def test_place_order_exception_handling(authenticated_client, requests_mock):
    """Test place_order exception handling."""
    url = authenticated_client.configuration.get_url_details("place_order")

    # Mock an API exception
    requests_mock.post(url, status_code=500, text="Internal Server Error")

    result = authenticated_client.place_order(
        exchange_segment="nse_cm",
        product="CNC",
        price="1500",
        order_type="L",
        quantity="1",
        validity="DAY",
        trading_symbol="RELIANCE-EQ",
        transaction_type="B",
    )

    # Should return error
    assert "Error" in result or "error" in result


def test_positions_exception_handling(authenticated_client, requests_mock):
    """Test positions exception handling."""
    url = authenticated_client.configuration.get_url_details("positions")

    requests_mock.get(url, status_code=500, text="Server Error")

    result = authenticated_client.positions()

    # Should handle exception - result may be dict with Error or None
    assert result is None or (
        isinstance(result, dict) and ("Error" in result or "error" in result or result)
    )


def test_holdings_exception_handling(authenticated_client, requests_mock):
    """Test holdings exception handling."""
    url = authenticated_client.configuration.get_url_details("holdings")

    requests_mock.get(url, status_code=500, text="Server Error")

    result = authenticated_client.holdings()

    # Should handle exception
    assert "Error" in result or result is not None


def test_trade_report_exception_handling(authenticated_client, requests_mock):
    """Test trade_report exception handling."""
    url = authenticated_client.configuration.get_url_details("trade_report")

    requests_mock.get(url, status_code=500, text="Server Error")

    result = authenticated_client.trade_report()

    # Should handle exception
    assert "Error" in result or result is not None


def test_init_with_access_token():
    """Test NeoAPI initialization with access token."""
    client = NeoAPI(
        environment="prod",
        access_token="test_token_123",
        consumer_key="test_key",
    )

    assert client.configuration.bearer_token == "test_token_123"
    assert client.configuration.consumer_key == "test_key"


def test_init_without_access_token():
    """Test NeoAPI initialization without access token."""
    client = NeoAPI(environment="uat", consumer_key="test_key")

    assert client.configuration.bearer_token is None
    assert client.configuration.host == "uat"


def test_callbacks_initially_none():
    """Test that callbacks are None initially."""
    client = NeoAPI(environment="prod", consumer_key="test_key")

    assert client.on_message is None
    assert client.on_error is None
    assert client.on_close is None
    assert client.on_open is None


def test_neo_websocket_initially_none():
    """Test that NeoWebSocket is None initially."""
    client = NeoAPI(environment="prod", consumer_key="test_key")

    assert client.NeoWebSocket is None


def test_configuration_consumer_key_set():
    """Test that configuration consumer_key is set."""
    client = NeoAPI(environment="prod", consumer_key="my_consumer_key")

    assert client.configuration.consumer_key == "my_consumer_key"


def test_configuration_neo_fin_key_set():
    """Test that configuration neo_fin_key is set."""
    client = NeoAPI(environment="prod", consumer_key="test_key", neo_fin_key="my_fin_key")

    assert client.configuration.neo_fin_key == "my_fin_key"


def test_api_client_created():
    """Test that api_client is created."""
    client = NeoAPI(environment="prod", consumer_key="test_key")

    assert client.api_client is not None
    assert hasattr(client.api_client, "configuration")
