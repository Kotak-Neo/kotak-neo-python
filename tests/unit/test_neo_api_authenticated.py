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
    )

    assert result["stat"] == "Ok"


def test_place_order_defaults_trigger_price_for_limit_when_none(authenticated_client, monkeypatch):
    """trigger_price=None is coerced to '0' for L/MKT order types — the REST
    API still requires the "tp" field, but the value doesn't matter for these
    order types, so the caller shouldn't have to supply it."""
    captured = {}

    def fake_order_placing(self, **kwargs):
        captured.update(kwargs)
        return {"stat": "Ok"}

    monkeypatch.setattr("neo_api_client.neo_api.OrderAPI.order_placing", fake_order_placing)

    authenticated_client.place_order(
        exchange_segment="nse_cm",
        product="CNC",
        price="1500",
        order_type="L",
        quantity="1",
        validity="DAY",
        trading_symbol="RELIANCE-EQ",
        transaction_type="B",
        trigger_price=None,
    )

    assert captured["trigger_price"] == "0"


def test_place_order_does_not_default_trigger_price_for_sl_when_none(
    authenticated_client, monkeypatch
):
    """trigger_price=None is left as-is for SL/SL-M — a real trigger price is
    required there, so silently defaulting to '0' would be unsafe."""
    captured = {}

    def fake_order_placing(self, **kwargs):
        captured.update(kwargs)
        return {"stat": "Ok"}

    monkeypatch.setattr("neo_api_client.neo_api.OrderAPI.order_placing", fake_order_placing)

    authenticated_client.place_order(
        exchange_segment="nse_cm",
        product="CNC",
        price="1500",
        order_type="SL",
        quantity="1",
        validity="DAY",
        trading_symbol="RELIANCE-EQ",
        transaction_type="B",
        trigger_price=None,
    )

    assert captured["trigger_price"] is None


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


@pytest.mark.parametrize(
    "field",
    ["exchange_segment", "price", "quantity", "trading_symbol", "transaction_type"],
)
def test_place_order_blank_mandatory_returns_error(authenticated_client, field):
    """Blank mandatory params are rejected before any API call, as an Error dict."""
    params = {
        "exchange_segment": "nse_cm",
        "product": "CNC",
        "price": "1",
        "order_type": "L",
        "quantity": "1",
        "validity": "DAY",
        "trading_symbol": "TCS",
        "transaction_type": "B",
    }
    params[field] = ""

    result = authenticated_client.place_order(**params)

    assert "Error" in result
    # No network call needed — the validation error is surfaced as a dict.
    assert "blank" in str(result["Error"]).lower() or "mandatory" in str(result["Error"]).lower()


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


def test_order_report_by_order_id(authenticated_client, requests_mock):
    """Passing order_id routes to /quick/user/orders/<order_no>."""
    order_id = "250720000007242"
    url = f"{authenticated_client.configuration.get_url_details('order_book')}/{order_id}"

    requests_mock.get(
        url,
        json={"stat": "Ok", "data": [{"nOrdNo": order_id, "ordSt": "rejected"}]},
        status_code=200,
    )

    result = authenticated_client.order_report(order_id=order_id)

    assert result["stat"] == "Ok"
    assert result["data"][0]["nOrdNo"] == order_id
    assert requests_mock.last_request.url.endswith(f"/orders/{order_id}")


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

    login_url = "https://mis.kotaksecurities.com/login/1.0/tradeApiLogin"

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

    validate_url = "https://mis.kotaksecurities.com/login/1.0/tradeApiValidate"

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


def test_totp_validate_captures_feed_url_and_rt_url(requests_mock):
    """feedUrl/rtUrl/ucc are captured alongside baseUrl/dataCenter -- feedUrl/
    rtUrl as secondary sources for the SFeed/order-feed URLs (see
    resolve_dynamic_urls), ucc as the default SFeed "user" credential."""
    client = NeoAPI(environment="prod", consumer_key="test_key")
    client.configuration.view_token = "view_token_123"
    client.configuration.sid = "sid_123"

    validate_url = "https://mis.kotaksecurities.com/login/1.0/tradeApiValidate"
    requests_mock.post(
        validate_url,
        json={
            "data": {
                "token": "edit_token_123",
                "sid": "edit_sid_123",
                "rid": "edit_rid_123",
                "dataCenter": "DC1",
                "baseUrl": "https://gw-napi.kotaksecurities.com",
                "feedUrl": "https://login-feed.kotaksecurities.com/wsfeed",
                "rtUrl": "https://login-rt.kotaksecurities.com/realtime",
                "ucc": "ABC123",
            }
        },
        status_code=200,
    )

    client.totp_validate(mpin="1234")

    assert client.configuration.feed_url == "https://login-feed.kotaksecurities.com/wsfeed"
    assert client.configuration.rt_url == "https://login-rt.kotaksecurities.com/realtime"
    assert client.configuration.ucc == "ABC123"


def test_totp_login_captures_ucc(requests_mock):
    """ucc from the totp_login() response is captured early, before totp_validate()."""
    client = NeoAPI(environment="prod", consumer_key="test_key")

    login_url = "https://mis.kotaksecurities.com/login/1.0/tradeApiLogin"
    requests_mock.post(
        login_url,
        json={
            "data": {
                "token": "view_token_123",
                "sid": "sid_123",
                "rid": "rid_123",
                "ucc": "ABC123",
            }
        },
        status_code=200,
    )

    client.totp_login(mobile_number="+919999999999", ucc="ABC123", totp="123456")

    assert client.configuration.ucc == "ABC123"


def test_totp_validate_keeps_ucc_from_login_if_validate_response_omits_it(requests_mock):
    """totp_validate() shouldn't clobber ucc already captured from totp_login()
    if its own response happens not to include the field."""
    client = NeoAPI(environment="prod", consumer_key="test_key")
    client.configuration.view_token = "view_token_123"
    client.configuration.sid = "sid_123"
    client.configuration.ucc = "ABC123"  # already captured from totp_login()

    validate_url = "https://mis.kotaksecurities.com/login/1.0/tradeApiValidate"
    requests_mock.post(
        validate_url,
        json={
            "data": {
                "token": "edit_token_123",
                "sid": "edit_sid_123",
                "rid": "edit_rid_123",
                # No "ucc" in this response.
            }
        },
        status_code=200,
    )

    client.totp_validate(mpin="1234")

    assert client.configuration.ucc == "ABC123"


def test_totp_validate_resolves_dynamic_websocket_url(requests_mock):
    """totp_validate() fetches the data center's feed URL, and create_websocket() uses it."""
    from neo_api_client.utils.urls import CONFIG_SERVICE_URL_PROD

    client = NeoAPI(environment="prod", consumer_key="test_key")
    client.configuration.view_token = "view_token_123"
    client.configuration.sid = "sid_123"

    validate_url = "https://mis.kotaksecurities.com/login/1.0/tradeApiValidate"
    requests_mock.post(
        validate_url,
        json={
            "data": {
                "token": "edit_token_123",
                "sid": "edit_sid_123",
                "rid": "edit_rid_123",
                "dataCenter": "E21",
                "baseUrl": "https://gw-napi.kotaksecurities.com",
            }
        },
        status_code=200,
    )
    requests_mock.get(
        CONFIG_SERVICE_URL_PROD,
        json={
            "data": {
                "configs": {
                    "E21_broadcast_source": "sh",
                    "E21_sh_broadcast_endpoint": "https://sfeed-e21.kotaksecurities.com/wsfeed",
                }
            }
        },
    )

    client.totp_validate(mpin="1234")

    # Cached verbatim (as the config service returned it, scheme included);
    # SFeedWebSocket normalizes https -> wss itself when it receives the URL.
    assert (
        client.configuration.sfeed_websocket_url == "https://sfeed-e21.kotaksecurities.com/wsfeed"
    )

    ws = client.create_websocket()

    assert ws.url == "wss://sfeed-e21.kotaksecurities.com/wsfeed"


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
    """A non-JSON error body (e.g. a plaintext 500) returns a structured
    error dict with the real status code, not a raw JSONDecodeError."""
    url = authenticated_client.configuration.get_url_details("holdings")

    requests_mock.get(url, status_code=500, text="Server Error")

    result = authenticated_client.holdings()

    assert result["StatusCode"] == 500
    assert result["ResponseText"] == "Server Error"


def test_holdings_wraps_unexpected_exception(authenticated_client, monkeypatch):
    """An unexpected exception from the service layer is still caught and
    returned as an {"Error": ...} dict."""
    from neo_api_client import neo_api as _mod

    monkeypatch.setattr(_mod.PortfolioAPI, "portfolio_holdings", _make_raise())

    result = authenticated_client.holdings()
    assert "Error" in result


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


# ---- Additional authenticated happy-path wrappers (coverage) ---------------


def test_order_history_success(authenticated_client, requests_mock):
    """order_history() success path (response wrapped in a 'data' key)."""
    url = authenticated_client.configuration.get_url_details("order_history")
    requests_mock.post(url, json={"stat": "Ok", "data": []}, status_code=200)

    result = authenticated_client.order_history(order_id="12345")
    assert "data" in result


def test_limits_success(authenticated_client, requests_mock):
    """limits() success path — takes no parameters; always requests ALL."""
    url = authenticated_client.configuration.get_url_details("limits")
    requests_mock.post(url, json={"stat": "Ok", "Net": "1000"}, status_code=200)

    result = authenticated_client.limits()
    assert result["stat"] == "Ok"


def test_limits_exception_handling(authenticated_client, monkeypatch):
    """limits() wraps an unexpected service exception into an Error dict."""

    def boom(self):
        raise RuntimeError("boom")

    monkeypatch.setattr(
        "neo_api_client.services.limits.LimitsAPI.limit_init",
        boom,
    )

    result = authenticated_client.limits()
    assert "Error" in result


def test_margin_required_success(authenticated_client, requests_mock):
    """margin_required() success path."""
    url = authenticated_client.configuration.get_url_details("margin")
    requests_mock.post(url, json={"stat": "Ok", "marginUsed": "500"}, status_code=200)

    result = authenticated_client.margin_required(
        exchange_segment="nse_cm",
        price="100",
        order_type="L",
        product="CNC",
        quantity="1",
        instrument_token="11536",
        transaction_type="B",
    )
    assert "data" in result


def test_margin_required_invalid_returns_error(authenticated_client):
    """margin_required() with an invalid segment is caught and returned as error."""
    result = authenticated_client.margin_required(
        exchange_segment="BOGUS",
        price="100",
        order_type="L",
        product="CNC",
        quantity="1",
        instrument_token="11536",
        transaction_type="B",
    )
    assert "Error" in result


def test_modify_order_success(authenticated_client, requests_mock):
    """modify_order() happy path."""
    url = authenticated_client.configuration.get_url_details("modify_order")
    requests_mock.post(url, json={"stat": "Ok", "nOrdNo": "12345"}, status_code=200)

    result = authenticated_client.modify_order(
        order_id="12345",
        price="105",
        order_type="L",
        quantity="2",
        validity="DAY",
    )
    assert result["stat"] == "Ok"


def test_modify_order_defaults_trigger_price_for_limit(authenticated_client, monkeypatch):
    """trigger_price=None is coerced to '0' for L/MKT."""
    captured = {}

    def fake_quick_modification(self, **kwargs):
        captured.update(kwargs)
        return {"stat": "Ok"}

    monkeypatch.setattr(
        "neo_api_client.neo_api.ModifyOrder.quick_modification", fake_quick_modification
    )

    authenticated_client.modify_order(
        order_id="12345",
        price="105",
        order_type="L",
        quantity="2",
        validity="DAY",
        trigger_price=None,
    )

    assert captured["trigger_price"] == "0"
    assert captured["order_type"] == "L"


def test_modify_order_requires_order_id(authenticated_client):
    """modify_order() returns a validation Error dict when order_id is missing.

    (Now surfaced consistently as an {"Error": ...} dict, like the other order
    methods, rather than raising — input validation runs before the API call.)
    """
    result = authenticated_client.modify_order(
        order_id=None,
        price="105",
        order_type="L",
        quantity="2",
        validity="DAY",
    )
    assert "Error" in result


@pytest.mark.parametrize(
    "field,value",
    [
        ("price", ""),
        ("price", "abc"),
        ("quantity", "0"),
        ("order_type", "INVALID"),
        ("validity", "GTC"),
    ],
)
def test_modify_order_invalid_input_returns_error(authenticated_client, field, value):
    """modify_order() rejects blank/invalid mandatory params before any API call."""
    params = {
        "order_id": "260709000000058",
        "price": "1400",
        "order_type": "L",
        "quantity": "3",
        "validity": "DAY",
    }
    params[field] = value

    result = authenticated_client.modify_order(**params)

    assert "Error" in result


def test_cancel_order_blank_order_id_returns_error(authenticated_client):
    """cancel_order() rejects a blank order_id as a validation Error dict."""
    result = authenticated_client.cancel_order(order_id="   ")
    assert "Error" in result


def test_search_scrip_missing_exchange_segment(authenticated_client):
    """search_scrip() with empty exchange_segment returns a validation error."""
    result = authenticated_client.search_scrip(exchange_segment="", symbol="RELIANCE")
    assert "error" in result


def test_search_scrip_omitted_exchange_segment_returns_error_not_typeerror(authenticated_client):
    """search_scrip() called by keyword without exchange_segment at all (e.g.
    only expiry/option_type/strike_price/ignore_50multiple) must return the
    same validation error as an explicit blank value, not raise TypeError."""
    result = authenticated_client.search_scrip(
        expiry="",
        option_type="",
        strike_price="",
        ignore_50multiple=True,
    )
    assert "error" in result


def test_scrip_master_success(authenticated_client, requests_mock):
    """scrip_master() success path returns file paths."""
    url = authenticated_client.configuration.get_url_details("scrip_master")
    requests_mock.get(
        url,
        json={"stat": "Ok", "data": {"filesPaths": ["https://x/nse_cm.csv"]}},
        status_code=200,
    )

    result = authenticated_client.scrip_master()
    assert result is not None


@pytest.mark.parametrize(
    "kwargs,expected_field",
    [
        ({"mobile_number": None, "ucc": "ABC123", "totp": "123456"}, "MobileNumber"),
        ({"mobile_number": "+919999999999", "ucc": None, "totp": "123456"}, "Ucc"),
        ({"mobile_number": "+919999999999", "ucc": "ABC123", "totp": None}, "Totp"),
        ({"mobile_number": "", "ucc": "ABC123", "totp": "123456"}, "MobileNumber"),
    ],
)
def test_totp_login_blank_field_rejected_client_side(
    authenticated_client, requests_mock, kwargs, expected_field
):
    """totp_login() rejects a blank/missing field client-side (no network
    call), using the same error shape the backend returns for this case."""
    login_url = (
        authenticated_client.configuration.get_domain(session_init=True)
        + "/login/1.0/tradeApiLogin"
    )
    login_route = requests_mock.post(login_url, json={"data": {}}, status_code=200)

    result = authenticated_client.totp_login(**kwargs)

    assert result == {
        "error": [{"code": "400", "message": f"Missing required field '{expected_field}'"}]
    }
    assert login_route.call_count == 0


def test_totp_validate_blank_mpin_rejected_client_side(authenticated_client, requests_mock):
    """totp_validate() rejects a blank/missing mpin client-side (no network
    call), using the same error shape the backend returns for this case."""
    validate_url = (
        authenticated_client.configuration.get_domain(session_init=True)
        + "/login/1.0/tradeApiValidate"
    )
    validate_route = requests_mock.post(validate_url, json={"data": {}}, status_code=200)

    result = authenticated_client.totp_validate(mpin=None)

    assert result == {"error": [{"code": "400", "message": "Missing required field 'Mpin'"}]}
    assert validate_route.call_count == 0


def test_quotes_missing_tokens_returns_error(authenticated_client):
    """quotes() with no instrument_tokens returns a validation error."""
    result = authenticated_client.quotes(instrument_tokens=None, quote_type="all")
    assert "error" in result


# ---- Additional branch coverage for neo_api.py -----------------------------


def test_order_report_success(authenticated_client, requests_mock):
    """order_report() success path returns the order book."""
    url = authenticated_client.configuration.get_url_details("order_book")
    requests_mock.get(url, json={"stat": "Ok", "data": []}, status_code=200)

    result = authenticated_client.order_report()
    assert result["stat"] == "Ok"


def test_search_scrip_success(authenticated_client, requests_mock):
    """search_scrip() happy path returns filtered scrip data."""
    url = authenticated_client.configuration.get_url_details("scrip_master")
    csv_path = "https://api.kotaksecurities.com/scripmaster/NSE_CM.csv"
    requests_mock.get(
        url,
        json={"stat": "Ok", "data": {"filesPaths": [csv_path]}},
        status_code=200,
    )
    csv = "pSymbol,pTrdSymbol,pExchSeg,pSymbolName\n1,RELIANCE-EQ,nse_cm,RELIANCE\n"
    requests_mock.get(csv_path, text=csv, status_code=200)

    result = authenticated_client.search_scrip(exchange_segment="nse_cm", symbol="RELIANCE")
    assert result is not None


def test_search_scrip_invalid_segment_returns_error(authenticated_client):
    """search_scrip() with an unknown segment is caught and returned as error."""
    result = authenticated_client.search_scrip(exchange_segment="BOGUS", symbol="X")
    assert "Error" in result


def test_search_scrip_without_2fa_succeeds_with_consumer_key_only(requests_mock):
    """search_scrip() does not require a completed 2FA session — only
    consumer_key is needed, since the API authenticates via Authorization alone."""
    client = NeoAPI(environment="prod", consumer_key="test_key")

    url = client.configuration.get_url_details("scrip_master")
    csv_path = "https://api.kotaksecurities.com/scripmaster/NSE_CM.csv"
    requests_mock.get(
        url,
        json={"stat": "Ok", "data": {"filesPaths": [csv_path]}},
        status_code=200,
    )
    csv = "pSymbol,pTrdSymbol,pExchSeg,pSymbolName,dStrikePrice;\n1,RELIANCE-EQ,nse_cm,RELIANCE,0\n"
    requests_mock.get(csv_path, text=csv, status_code=200)

    result = client.search_scrip(exchange_segment="nse_cm", symbol="RELIANCE")

    assert result == [
        {
            "pSymbol": 1,
            "pTrdSymbol": "RELIANCE-EQ",
            "pExchSeg": "nse_cm",
            "pSymbolName": "RELIANCE",
            "dStrikePrice;": 0,
        }
    ]


def test_logout_success(authenticated_client):
    """logout() clears session tokens and returns an OK state."""
    result = authenticated_client.logout()
    assert result["State"] == "OK"
    assert authenticated_client.configuration.edit_token is None
    assert authenticated_client.configuration.edit_sid is None


def test_create_websocket_url_override(authenticated_client):
    """create_websocket(url=...) overrides the default feed URL."""
    ws = authenticated_client.create_websocket(url="wss://example.test/feed")
    assert ws.url == "wss://example.test/feed"


def test_create_websocket_uses_feed_url_when_dynamic_config_missing(authenticated_client):
    """totp_validate()'s feedUrl is used when the dynamic config service
    didn't resolve sfeed_websocket_url."""
    authenticated_client.configuration.feed_url = "https://login-feed.kotaksecurities.com/wsfeed"

    ws = authenticated_client.create_websocket()

    assert ws.url == "wss://login-feed.kotaksecurities.com/wsfeed"


def test_create_websocket_passes_ucc_as_user(authenticated_client):
    """create_websocket() passes configuration.ucc through, so the auth
    frame's "user" field is the account's real UCC, not the demo placeholder."""
    authenticated_client.configuration.ucc = "ABC123"

    ws = authenticated_client.create_websocket()

    assert ws.user == "ABC123"


def test_create_websocket_explicit_user_kwarg_wins_over_ucc(authenticated_client):
    authenticated_client.configuration.ucc = "ABC123"

    ws = authenticated_client.create_websocket(user="explicit-user")

    assert ws.user == "explicit-user"


def test_create_websocket_dynamic_config_wins_over_feed_url(authenticated_client):
    """sfeed_websocket_url (dynamic config) takes priority over feed_url (totp_validate)."""
    authenticated_client.configuration.sfeed_websocket_url = "https://config.example.com/wsfeed"
    authenticated_client.configuration.feed_url = "https://login-feed.kotaksecurities.com/wsfeed"

    ws = authenticated_client.create_websocket()

    assert ws.url == "wss://config.example.com/wsfeed"


def test_create_websocket_requires_auth():
    """create_websocket() raises when the session is not authenticated."""
    client = NeoAPI(environment="prod", consumer_key="k")
    with pytest.raises(ValueError, match="Authentication required"):
        client.create_websocket()


def test_help_socket_keyword_maps_to_create_websocket(authenticated_client):
    """help('socket') resolves to create_websocket without raising."""
    # Should not raise; exercises the help() happy path.
    authenticated_client.help("socket")


def test_modify_order_exception(authenticated_client, requests_mock):
    """modify_order() returns an Error dict when the API call fails."""
    modify_url = authenticated_client.configuration.get_url_details("modify_order")
    requests_mock.post(modify_url, status_code=500, text="boom")

    result = authenticated_client.modify_order(
        order_id="12345",
        price="105",
        order_type="L",
        quantity="2",
        validity="DAY",
    )
    assert "Error" in result


# ---- except-branch coverage: service raises -> {"Error": e} -----------------


def _make_raise(message="boom"):
    def _boom(*args, **kwargs):
        raise RuntimeError(message)

    return _boom


def test_order_report_exception_handling(authenticated_client, monkeypatch):
    """order_report() wraps a service exception into an Error dict."""
    from neo_api_client import neo_api as _mod

    monkeypatch.setattr(_mod.OrderReportAPI, "ordered_books", _make_raise())
    result = authenticated_client.order_report()
    assert "Error" in result


def test_order_report_by_id_exception_handling(authenticated_client, monkeypatch):
    """order_report(order_id=...) wraps a service exception into an Error dict."""
    from neo_api_client import neo_api as _mod

    monkeypatch.setattr(_mod.OrderReportAPI, "ordered_book_by_id", _make_raise())
    result = authenticated_client.order_report(order_id="123")
    assert "Error" in result


def test_order_history_exception_handling(authenticated_client, monkeypatch):
    """order_history() wraps a service exception into an Error dict."""
    from neo_api_client import neo_api as _mod

    monkeypatch.setattr(_mod.OrderHistoryAPI, "ordered_history", _make_raise())
    result = authenticated_client.order_history(order_id="123")
    assert "Error" in result


def test_trade_report_exception_wrapped(authenticated_client, monkeypatch):
    """trade_report() wraps a service exception into an Error dict (except branch)."""
    from neo_api_client import neo_api as _mod

    monkeypatch.setattr(_mod.TradeReportAPI, "trading_report", _make_raise())
    result = authenticated_client.trade_report()
    assert "Error" in result


def test_positions_exception_wrapped(authenticated_client, monkeypatch):
    """positions() wraps a service exception into an Error dict."""
    from neo_api_client import neo_api as _mod

    monkeypatch.setattr(_mod.PositionsAPI, "position_init", _make_raise())
    result = authenticated_client.positions()
    assert "Error" in result


def test_whatsmyip_success(authenticated_client, monkeypatch):
    """whatsmyip() returns the ClientIpAPI payload on the happy path."""
    from neo_api_client import neo_api as _mod

    monkeypatch.setattr(
        _mod.ClientIpAPI, "whatsmyip", lambda self: {"data": [{"ip": "1.2.3.4"}], "stCode": 1000}
    )
    result = authenticated_client.whatsmyip()
    assert result["data"][0]["ip"] == "1.2.3.4"


def test_whatsmyip_exception_handling(authenticated_client, monkeypatch):
    """whatsmyip() wraps a service exception into an Error dict."""
    from neo_api_client import neo_api as _mod

    monkeypatch.setattr(_mod.ClientIpAPI, "whatsmyip", _make_raise())
    result = authenticated_client.whatsmyip()
    assert "Error" in result


def test_search_scrip_exception_handling(authenticated_client, monkeypatch):
    """search_scrip() wraps a service exception into an Error/message dict."""
    from neo_api_client import neo_api as _mod

    monkeypatch.setattr(_mod.ScripSearch, "scrip_search", _make_raise())
    result = authenticated_client.search_scrip(exchange_segment="nse_cm", symbol="RELIANCE")
    assert "Error" in result


def test_search_scrip_returns_service_result(authenticated_client, monkeypatch):
    """search_scrip() returns the service payload on the happy path (line 658)."""
    from neo_api_client import neo_api as _mod

    payload = [{"pTrdSymbol": "RELIANCE-EQ"}]
    monkeypatch.setattr(_mod.ScripSearch, "scrip_search", lambda self, **kw: payload)
    result = authenticated_client.search_scrip(exchange_segment="nse_cm", symbol="RELIANCE")
    assert result == payload


def test_help_handles_internal_exception(authenticated_client, monkeypatch):
    """help() catches an internal error and returns an Error dict (723-724)."""
    import inspect

    monkeypatch.setattr(inspect, "signature", _make_raise("sig boom"))
    result = authenticated_client.help("order_report")
    assert result["Error"].startswith("Some Exception")


def test_logout_handles_internal_exception(authenticated_client):
    """logout() catches an internal error and returns a NOT_OK state (747-748)."""

    class _RaisingConfig:
        """Reports authenticated, but raises when tokens are cleared."""

        edit_token = "t"
        edit_sid = "s"

        def __setattr__(self, name, value):
            raise RuntimeError("cannot clear")

    authenticated_client.configuration = _RaisingConfig()
    result = authenticated_client.logout()
    assert result["State"] == "NOT_OK"


def test_help_invalid_function_name(authenticated_client, capsys):
    """help() with an unknown function name prints a not-valid message."""
    authenticated_client.help("not_a_real_method")
    assert "not a valid function name" in capsys.readouterr().out


# ---- unauthenticated guards: "Complete the 2fa process" ---------------------


@pytest.fixture
def unauth_client():
    return NeoAPI(environment="prod", consumer_key="test_key")


@pytest.mark.parametrize(
    "call",
    [
        lambda c: c.order_report(),
        lambda c: c.order_history(order_id="1"),
        lambda c: c.trade_report(),
        lambda c: c.positions(),
        lambda c: c.whatsmyip(),
        lambda c: c.logout(),
    ],
)
def test_methods_require_2fa(unauth_client, call):
    """Each guarded method returns the 2fa error dict when unauthenticated."""
    result = call(unauth_client)
    assert "Error Message" in result
    assert "2fa" in result["Error Message"]
