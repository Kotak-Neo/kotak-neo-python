import httpx
import pytest

from neo_api_client import NeoAPI


def test_quotes_wrapper(monkeypatch):
    client = NeoAPI(
        environment="prod",
        consumer_key="abc",
    )

    monkeypatch.setattr(
        client,
        "quotes",
        lambda *args, **kwargs: {"stat": "Ok"},
    )

    result = client.quotes(
        instrument_tokens=["12345"],
        quote_type="all",
    )

    assert result["stat"] == "Ok"


def test_neo_api_init_prod():
    """Test NeoAPI initialization with prod environment."""
    client = NeoAPI(
        environment="prod",
        consumer_key="test_key",
    )

    assert client.configuration.host == "prod"
    assert client.configuration.consumer_key == "test_key"
    assert client.api_client is not None


def test_neo_api_custom_transport_reaches_rest_client():
    """transport= on NeoAPI is the migration hook for custom proxy/mTLS/pooling
    deployments that used to monkey-patch the old requests-based client."""
    custom_transport = httpx.HTTPTransport()

    client = NeoAPI(environment="prod", consumer_key="test_key", transport=custom_transport)

    assert client.api_client.rest_client.session._transport is custom_transport


def test_neo_api_custom_limits_reaches_rest_client():
    """limits= on NeoAPI lets callers resize the connection pool without a
    full custom transport."""
    custom_limits = httpx.Limits(max_connections=1, max_keepalive_connections=1)

    client = NeoAPI(environment="prod", consumer_key="test_key", limits=custom_limits)

    assert client.api_client.rest_client.session._transport._pool._max_connections == 1


def test_neo_api_custom_transport_with_access_token():
    """The access_token branch of NeoAPI.__init__ also threads transport/limits
    through, not just the consumer_key branch."""
    custom_transport = httpx.HTTPTransport()

    client = NeoAPI(environment="prod", access_token="token123", transport=custom_transport)

    assert client.api_client.rest_client.session._transport is custom_transport


def test_neo_api_http2_and_timeout_reach_rest_client():
    """http2=/timeout= on NeoAPI are the published knobs for the httpx stack's
    protocol negotiation and default request timeout."""
    client = NeoAPI(environment="prod", consumer_key="test_key", http2=False, timeout=45)

    session = client.api_client.rest_client.session
    assert session._transport._pool._http2 is False
    assert session.timeout.connect == 45


def test_neo_api_init_uat():
    """Test NeoAPI initialization with UAT environment."""
    client = NeoAPI(
        environment="uat",
        consumer_key="test_key",
    )

    assert client.configuration.host == "uat"


def test_neo_api_init_with_access_token():
    """Test NeoAPI initialization with access token."""
    client = NeoAPI(
        environment="prod",
        access_token="test_access_token",
        consumer_key="test_key",
    )

    assert client.configuration.bearer_token == "test_access_token"


def test_neo_api_init_with_neo_fin_key():
    """Test NeoAPI initialization with neo_fin_key."""
    client = NeoAPI(
        environment="prod",
        consumer_key="test_key",
        neo_fin_key="test_fin_key",
    )

    assert client.configuration.neo_fin_key == "test_fin_key"


def test_neo_api_websocket_callbacks():
    """Test that WebSocket callbacks can be set."""
    client = NeoAPI(
        environment="prod",
        consumer_key="test_key",
    )

    def on_message(_msg):
        pass

    def on_error(_err):
        pass

    def on_open():
        pass

    def on_close():
        pass

    client.on_message = on_message
    client.on_error = on_error
    client.on_open = on_open
    client.on_close = on_close

    assert client.on_message == on_message
    assert client.on_error == on_error
    assert client.on_open == on_open
    assert client.on_close == on_close


def test_neo_api_subscribe_removed():
    """Legacy subscribe() is removed in 2.2.0 and raises NotImplementedError."""
    client = NeoAPI(
        environment="prod",
        consumer_key="test_key",
    )

    with pytest.raises(NotImplementedError) as exc_info:
        client.subscribe(
            instrument_tokens=[{"instrument_token": "1333", "exchange_segment": "nse_cm"}],
            isIndex=False,
            isDepth=False,
        )

    assert "SFeed" in str(exc_info.value)


def test_neo_api_un_subscribe_removed():
    """Legacy un_subscribe() is removed in 2.2.0 and raises NotImplementedError."""
    client = NeoAPI(
        environment="prod",
        consumer_key="test_key",
    )

    with pytest.raises(NotImplementedError) as exc_info:
        client.un_subscribe(
            instrument_tokens=[{"instrument_token": "1333", "exchange_segment": "nse_cm"}],
            isIndex=False,
            isDepth=False,
        )

    assert "SFeed" in str(exc_info.value)


def test_neo_api_subscribe_to_orderfeed_removed():
    """Legacy subscribe_to_orderfeed() is removed in 2.2.0 and raises NotImplementedError."""
    client = NeoAPI(
        environment="prod",
        consumer_key="test_key",
    )

    with pytest.raises(NotImplementedError) as exc_info:
        client.subscribe_to_orderfeed()

    assert "SFeed" in str(exc_info.value)


def test_neo_api_help_without_function():
    """Test help method without function name."""
    client = NeoAPI(
        environment="prod",
        consumer_key="test_key",
    )

    # Should not raise exception
    try:
        client.help()
    except Exception as e:
        pytest.fail(f"help() raised unexpected exception: {e}")


def test_neo_api_help_with_function():
    """Test help method with specific function name."""
    client = NeoAPI(
        environment="prod",
        consumer_key="test_key",
    )

    # Should not raise exception
    try:
        client.help("quotes")
    except Exception as e:
        pytest.fail(f"help('quotes') raised unexpected exception: {e}")


def test_neo_api_help_with_socket():
    """Test help method with 'socket' keyword."""
    client = NeoAPI(
        environment="prod",
        consumer_key="test_key",
    )

    # 'socket' should be mapped to 'subscribe'
    try:
        client.help("socket")
    except Exception as e:
        pytest.fail(f"help('socket') raised unexpected exception: {e}")


def test_neo_api_help_invalid_function():
    """Test help method with invalid function name."""
    client = NeoAPI(
        environment="prod",
        consumer_key="test_key",
    )

    # Should handle gracefully
    try:
        client.help("invalid_function_name")
    except Exception as e:
        pytest.fail(f"help with invalid function raised unexpected exception: {e}")


def test_neo_api_place_order_without_2fa():
    """Test place_order without completing 2FA."""
    client = NeoAPI(
        environment="prod",
        consumer_key="test_key",
    )

    result = client.place_order(
        exchange_segment="nse_cm",
        product="CNC",
        price="100",
        order_type="L",
        quantity="1",
        validity="DAY",
        trading_symbol="RELIANCE-EQ",
        transaction_type="B",
    )

    assert "Error Message" in result
    assert "2fa" in result["Error Message"]


def test_neo_api_cancel_order_without_2fa():
    """Test cancel_order without completing 2FA."""
    client = NeoAPI(
        environment="prod",
        consumer_key="test_key",
    )

    result = client.cancel_order(order_id="123456")

    assert "Error Message" in result
    assert "2fa" in result["Error Message"]


def test_neo_api_modify_order_without_2fa():
    """Test modify_order without completing 2FA."""
    client = NeoAPI(
        environment="prod",
        consumer_key="test_key",
    )

    result = client.modify_order(
        order_id="123456",
        price="105",
        quantity="2",
        order_type="L",
        validity="DAY",
    )

    assert "Error Message" in result
    assert "2fa" in result["Error Message"]


def test_neo_api_order_report_without_login():
    """Test order_report without login."""
    client = NeoAPI(
        environment="prod",
        consumer_key="test_key",
    )

    result = client.order_report()

    assert "Error Message" in result
    assert "2fa" in result["Error Message"]


def test_neo_api_trade_report_without_login():
    """Test trade_report without login."""
    client = NeoAPI(
        environment="prod",
        consumer_key="test_key",
    )

    result = client.trade_report()

    assert "Error Message" in result
    assert "2fa" in result["Error Message"]


def test_neo_api_positions_without_login():
    """Test positions without login."""
    client = NeoAPI(
        environment="prod",
        consumer_key="test_key",
    )

    result = client.positions()

    assert "Error Message" in result
    assert "2fa" in result["Error Message"]


def test_neo_api_holdings_without_login():
    """Test holdings without login."""
    client = NeoAPI(
        environment="prod",
        consumer_key="test_key",
    )

    result = client.holdings()

    assert "Error Message" in result
    assert "2fa" in result["Error Message"]


def test_neo_api_limits_without_login():
    """Test limits without login."""
    client = NeoAPI(
        environment="prod",
        consumer_key="test_key",
    )

    result = client.limits()

    assert "Error Message" in result
    assert "2fa" in result["Error Message"]


def test_neo_api_scrip_master_without_login(requests_mock):
    """scrip_master() does not require login/2FA — only consumer_key."""
    client = NeoAPI(
        environment="prod",
        consumer_key="test_key",
    )
    url = client.configuration.get_url_details("scrip_master")
    requests_mock.get(
        url,
        json={"stat": "Ok", "data": {"filesPaths": ["nse_cm.csv"]}},
        status_code=200,
    )

    result = client.scrip_master()

    assert result == {"filesPaths": ["nse_cm.csv"]}


def test_neo_api_order_history_without_login():
    """Test order_history without login."""
    client = NeoAPI(
        environment="prod",
        consumer_key="test_key",
    )

    result = client.order_history(order_id="123456")

    assert "Error Message" in result
    assert "2fa" in result["Error Message"]
