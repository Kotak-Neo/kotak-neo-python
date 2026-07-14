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
        market_protection="0",
        pf="N",
        trigger_price="100",
        tag="test_tag",
        scrip_token="11536",
        square_off_type="Absolute",
        stop_loss_type="Absolute",
        stop_loss_value="95",
        square_off_value="105",
        last_traded_price="100.50",
        trailing_stop_loss="YES",
        trailing_sl_value="2",
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


def test_order_cancelling_with_verification_pending(api_client, requests_mock):
    """Test order cancellation with verification - order is pending"""
    order_api_instance = OrderAPI(api_client)
    order_book_url = api_client.configuration.get_url_details("order_book")
    cancel_url = api_client.configuration.get_url_details("cancel_order")

    order_book_response = {
        "data": [
            {"nOrdNo": "12345", "ordSt": "pending", "rejRsn": ""},
        ]
    }
    cancel_response = {"stat": "Ok", "result": "cancelled"}

    requests_mock.get(order_book_url, json=order_book_response)
    requests_mock.post(cancel_url, json=cancel_response)

    result = order_api_instance.order_cancelling(order_id="12345", isVerify=True)

    assert result["stat"] == "Ok"


def test_order_cancelling_with_verification_rejected(api_client, requests_mock):
    """Test order cancellation with verification - order is rejected"""
    order_api_instance = OrderAPI(api_client)
    url = api_client.configuration.get_url_details("order_book")

    order_book_response = {
        "data": [
            {"nOrdNo": "12345", "ordSt": "rejected", "rejRsn": "Insufficient funds"},
        ]
    }

    requests_mock.get(url, json=order_book_response)

    result = order_api_instance.order_cancelling(order_id="12345", isVerify=True)

    assert result["status_code"] == 409
    assert result["ordSt"] == "rejected"
    assert result["Reason"] == "Insufficient funds"


def test_order_cancelling_with_verification_complete(api_client, requests_mock):
    """Test order cancellation with verification - order is complete"""
    order_api_instance = OrderAPI(api_client)
    url = api_client.configuration.get_url_details("order_book")

    order_book_response = {
        "data": [
            {"nOrdNo": "12345", "ordSt": "complete", "rejRsn": ""},
        ]
    }

    requests_mock.get(url, json=order_book_response)

    result = order_api_instance.order_cancelling(order_id="12345", isVerify=True)

    assert result["status_code"] == 409
    assert result["ordSt"] == "complete"


def test_order_cancelling_with_verification_cancelled(api_client, requests_mock):
    """Test order cancellation with verification - order is already cancelled"""
    order_api_instance = OrderAPI(api_client)
    url = api_client.configuration.get_url_details("order_book")

    order_book_response = {
        "data": [
            {"nOrdNo": "12345", "ordSt": "cancelled", "rejRsn": "User cancelled"},
        ]
    }

    requests_mock.get(url, json=order_book_response)

    result = order_api_instance.order_cancelling(order_id="12345", isVerify=True)

    assert result["status_code"] == 409
    assert result["ordSt"] == "cancelled"


def test_order_cancelling_with_amo(api_client, requests_mock):
    """Test order cancellation with AMO parameter"""
    order_api_instance = OrderAPI(api_client)
    url = api_client.configuration.get_url_details("cancel_order")
    mock_response = {"stat": "Ok", "result": "cancelled"}
    requests_mock.post(url, json=mock_response)

    result = order_api_instance.order_cancelling(order_id="12345", isVerify=False, amo="YES")

    assert result["stat"] == "Ok"


def test_order_cancelling_verify_order_book_without_data(api_client, requests_mock):
    """Verify path where the order book has no 'data' key -> falls through to
    the actual cancel (order.py 87->102 branch)."""
    order_api_instance = OrderAPI(api_client)
    order_book_url = api_client.configuration.get_url_details("order_book")
    cancel_url = api_client.configuration.get_url_details("cancel_order")

    # No "data" key at all -> the verification block is skipped.
    requests_mock.get(order_book_url, json={"stat": "Not_Ok", "emsg": "no orders"})
    requests_mock.post(cancel_url, json={"stat": "Ok", "result": "cancelled"})

    result = order_api_instance.order_cancelling(order_id="12345", isVerify=True)

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
    url = api_client.configuration.get_url_details("order_book")

    order_book_response = {
        "data": [
            {"nOrdNo": "12345", "ordSt": "cancelled", "rejRsn": ""},
        ]
    }

    requests_mock.get(url, json=order_book_response)

    result = order_api_instance.order_cancelling(order_id=" 12345 ", isVerify=True)

    assert "Error" in result


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
