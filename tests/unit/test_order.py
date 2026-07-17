import json
from urllib.parse import parse_qs

from neo_api_client.services.order import OrderAPI


def _sent_body(requests_mock):
    """Decode the form-encoded jData body from the last request."""
    return json.loads(parse_qs(requests_mock.last_request.text)["jData"][0])


def test_order_placing_success(api_client, requests_mock):
    """Test successful order placement"""
    order_api_instance = OrderAPI(api_client)
    url = api_client.configuration.get_url_details("place_order")
    mock_response = {"stat": "Ok", "nOrdNo": "12345"}
    requests_mock.post(url, json=mock_response)

    result = order_api_instance.order_placing(
        exchange_segment="nse_cm",
        product="CNC",
        price="100.50",
        order_type="L",
        quantity="10",
        validity="DAY",
        trading_symbol="RELIANCE-EQ",
        transaction_type="B",
    )

    assert result["stat"] == "Ok"
    assert result["nOrdNo"] == "12345"


def test_order_placing_with_optional_params(api_client, requests_mock):
    """Test order placement with optional parameters"""
    order_api_instance = OrderAPI(api_client)
    url = api_client.configuration.get_url_details("place_order")
    mock_response = {"stat": "Ok", "nOrdNo": "12345"}
    requests_mock.post(url, json=mock_response)

    result = order_api_instance.order_placing(
        exchange_segment="nse_cm",
        product="CNC",
        price="100.50",
        order_type="L",
        quantity="10",
        validity="DAY",
        trading_symbol="RELIANCE-EQ",
        transaction_type="B",
        amo="YES",
        disclosed_quantity="5",
        trigger_price="100",
    )

    assert result["stat"] == "Ok"
    assert result["nOrdNo"] == "12345"


def test_order_placing_api_exception(api_client, monkeypatch):
    """Test order placement with API exception"""
    from neo_api_client.exceptions import ApiException

    order_api_instance = OrderAPI(api_client)

    def fake_request(*args, **kwargs):
        raise ApiException(status=400, reason="Bad Request")

    monkeypatch.setattr(api_client.rest_client, "request", fake_request)

    result = order_api_instance.order_placing(
        exchange_segment="nse_cm",
        product="CNC",
        price="100.50",
        order_type="L",
        quantity="10",
        validity="DAY",
        trading_symbol="RELIANCE-EQ",
        transaction_type="B",
    )

    assert "error" in result


def test_order_cancelling_success(api_client, requests_mock):
    """Test successful order cancellation without verification"""
    order_api_instance = OrderAPI(api_client)
    url = api_client.configuration.get_url_details("cancel_order")
    mock_response = {"stat": "Ok", "result": "cancelled"}
    requests_mock.post(url, json=mock_response)

    result = order_api_instance.order_cancelling(order_id="12345", isVerify=False)

    assert result["stat"] == "Ok"
    assert result["result"] == "cancelled"


def test_order_cancelling_isverify_true_still_sends_directly(api_client, requests_mock):
    """isVerify no longer changes behavior — the cancel is always sent
    straight to the backend, regardless of the order's order-book status."""
    order_api_instance = OrderAPI(api_client)
    cancel_url = api_client.configuration.get_url_details("cancel_order")

    cancel_route = requests_mock.post(cancel_url, json={"stat": "Ok", "result": "cancelled"})

    result = order_api_instance.order_cancelling(order_id="12345", isVerify=True)

    assert result["stat"] == "Ok"
    assert cancel_route.call_count == 1


def test_order_cancelling_flags_already_complete_as_409(api_client, requests_mock):
    """The backend's 'order already complete' rejection (stCode 1021) is
    annotated with status_code 409 so callers can detect it without knowing
    the backend's internal stCode."""
    order_api_instance = OrderAPI(api_client)
    url = api_client.configuration.get_url_details("cancel_order")
    requests_mock.post(
        url,
        json={
            "stCode": 1021,
            "errMsg": "order is completed",
            "stat": "please provide valid order number",
        },
    )

    result = order_api_instance.order_cancelling(order_id="12345", isVerify=False)

    assert result["status_code"] == 409
    assert result["stCode"] == 1021
    assert result["errMsg"] == "order is completed"


def test_order_cancelling_with_amo(api_client, requests_mock):
    """Test order cancellation with AMO parameter"""
    order_api_instance = OrderAPI(api_client)
    url = api_client.configuration.get_url_details("cancel_order")
    mock_response = {"stat": "Ok", "result": "cancelled"}
    requests_mock.post(url, json=mock_response)

    result = order_api_instance.order_cancelling(order_id="12345", isVerify=False, amo="YES")

    assert result["stat"] == "Ok"


def test_order_cancelling_api_exception(api_client, monkeypatch):
    """Test order cancellation with API exception"""
    from neo_api_client.exceptions import ApiException

    order_api_instance = OrderAPI(api_client)

    def fake_request(*args, **kwargs):
        raise ApiException(status=500, reason="Internal Server Error")

    monkeypatch.setattr(api_client.rest_client, "request", fake_request)

    result = order_api_instance.order_cancelling(order_id="12345", isVerify=False)

    assert "error" in result


def test_order_cancelling_with_whitespace(api_client, requests_mock):
    """Test order cancellation with order_id containing whitespace"""
    order_api_instance = OrderAPI(api_client)
    url = api_client.configuration.get_url_details("cancel_order")

    requests_mock.post(url, json={"stat": "Ok", "result": "cancelled"})

    result = order_api_instance.order_cancelling(order_id=" 12345 ", isVerify=True)

    assert result["stat"] == "Ok"


# ---- "mp" (market protection) is always "0", not caller-configurable -------


def test_place_order_always_sends_mp_zero(api_client, requests_mock):
    """market_protection ("mp") is hardcoded to "0" and cannot be overridden."""
    requests_mock.post(api_client.configuration.get_url_details("place_order"), json={"stat": "Ok"})
    OrderAPI(api_client).order_placing(
        exchange_segment="bse_cm",
        product="NRML",
        price="3000",
        order_type="L",
        quantity="1",
        validity="DAY",
        trading_symbol="TCS",
        transaction_type="B",
    )
    assert _sent_body(requests_mock)["mp"] == "0"


# ---- "am" (AMO flag) is mandatory on every order request --------------------


def test_place_order_defaults_am_to_no(api_client, requests_mock):
    """Place order always sends am='NO' when amo isn't provided (mandatory)."""
    requests_mock.post(api_client.configuration.get_url_details("place_order"), json={"stat": "Ok"})
    OrderAPI(api_client).order_placing(
        exchange_segment="bse_cm",
        product="NRML",
        price="3000",
        order_type="L",
        quantity="1",
        validity="DAY",
        trading_symbol="TCS",
        transaction_type="B",
    )
    assert _sent_body(requests_mock)["am"] == "NO"


def test_place_order_amo_none_coerced_to_no(api_client, requests_mock):
    """Explicit amo=None must not leak am=null; it is coerced to 'NO'."""
    requests_mock.post(api_client.configuration.get_url_details("place_order"), json={"stat": "Ok"})
    OrderAPI(api_client).order_placing(
        exchange_segment="bse_cm",
        product="NRML",
        price="3000",
        order_type="L",
        quantity="1",
        validity="DAY",
        trading_symbol="TCS",
        transaction_type="B",
        amo=None,
    )
    assert _sent_body(requests_mock)["am"] == "NO"


def test_place_order_amo_yes_is_sent(api_client, requests_mock):
    """amo='YES' is passed through for AMO orders."""
    requests_mock.post(api_client.configuration.get_url_details("place_order"), json={"stat": "Ok"})
    OrderAPI(api_client).order_placing(
        exchange_segment="bse_cm",
        product="NRML",
        price="3000",
        order_type="L",
        quantity="1",
        validity="DAY",
        trading_symbol="TCS",
        transaction_type="B",
        amo="YES",
    )
    assert _sent_body(requests_mock)["am"] == "YES"


def test_cancel_order_defaults_am_to_no(api_client, requests_mock):
    """Cancel order always sends a valid am (default 'NO')."""
    requests_mock.post(
        api_client.configuration.get_url_details("cancel_order"), json={"stat": "Ok"}
    )
    OrderAPI(api_client).order_cancelling(order_id="260709000000058", isVerify=False, amo=None)
    body = _sent_body(requests_mock)
    assert body["on"] == "260709000000058"
    assert body["am"] == "NO"


def test_cancel_order_amo_yes_is_sent(api_client, requests_mock):
    """Cancel order forwards amo='YES' for AMO cancellations."""
    requests_mock.post(
        api_client.configuration.get_url_details("cancel_order"), json={"stat": "Ok"}
    )
    OrderAPI(api_client).order_cancelling(order_id="260709000000058", isVerify=False, amo="YES")
    assert _sent_body(requests_mock)["am"] == "YES"
