from neo_api_client.services.order import OrderAPI


def test_order_placing_success(api_client, requests_mock):
    """Test successful order placement"""
    api_client.configuration.serverId = "test_server"
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
    api_client.configuration.serverId = "test_server"
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

    api_client.configuration.serverId = "test_server"
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
    api_client.configuration.serverId = "test_server"
    order_api_instance = OrderAPI(api_client)
    url = api_client.configuration.get_url_details("cancel_order")
    mock_response = {"stat": "Ok", "result": "cancelled"}
    requests_mock.post(url, json=mock_response)

    result = order_api_instance.order_cancelling(order_id="12345", isVerify=False)

    assert result["stat"] == "Ok"
    assert result["result"] == "cancelled"


def test_order_cancelling_with_verification_pending(api_client, requests_mock):
    """Test order cancellation with verification - order is pending"""
    api_client.configuration.serverId = "test_server"
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
    api_client.configuration.serverId = "test_server"
    order_api_instance = OrderAPI(api_client)
    url = api_client.configuration.get_url_details("order_book")

    order_book_response = {
        "data": [
            {"nOrdNo": "12345", "ordSt": "rejected", "rejRsn": "Insufficient funds"},
        ]
    }

    requests_mock.get(url, json=order_book_response)

    result = order_api_instance.order_cancelling(order_id="12345", isVerify=True)

    assert "Error" in result
    assert result["Error"] == "The Given Order Status is rejected"
    assert result["Reason"] == "Insufficient funds"


def test_order_cancelling_with_verification_complete(api_client, requests_mock):
    """Test order cancellation with verification - order is complete"""
    api_client.configuration.serverId = "test_server"
    order_api_instance = OrderAPI(api_client)
    url = api_client.configuration.get_url_details("order_book")

    order_book_response = {
        "data": [
            {"nOrdNo": "12345", "ordSt": "complete", "rejRsn": ""},
        ]
    }

    requests_mock.get(url, json=order_book_response)

    result = order_api_instance.order_cancelling(order_id="12345", isVerify=True)

    assert "Error" in result
    assert result["Error"] == "The Given Order Status is Traded"


def test_order_cancelling_with_verification_cancelled(api_client, requests_mock):
    """Test order cancellation with verification - order is already cancelled"""
    api_client.configuration.serverId = "test_server"
    order_api_instance = OrderAPI(api_client)
    url = api_client.configuration.get_url_details("order_book")

    order_book_response = {
        "data": [
            {"nOrdNo": "12345", "ordSt": "cancelled", "rejRsn": "User cancelled"},
        ]
    }

    requests_mock.get(url, json=order_book_response)

    result = order_api_instance.order_cancelling(order_id="12345", isVerify=True)

    assert "Error" in result
    assert result["Error"] == "The Given Order Status is cancelled"


def test_order_cancelling_with_amo(api_client, requests_mock):
    """Test order cancellation with AMO parameter"""
    api_client.configuration.serverId = "test_server"
    order_api_instance = OrderAPI(api_client)
    url = api_client.configuration.get_url_details("cancel_order")
    mock_response = {"stat": "Ok", "result": "cancelled"}
    requests_mock.post(url, json=mock_response)

    result = order_api_instance.order_cancelling(order_id="12345", isVerify=False, amo="YES")

    assert result["stat"] == "Ok"


def test_order_cancelling_api_exception(api_client, monkeypatch):
    """Test order cancellation with API exception"""
    from neo_api_client.exceptions import ApiException

    api_client.configuration.serverId = "test_server"
    order_api_instance = OrderAPI(api_client)

    def fake_request(*args, **kwargs):
        raise ApiException(status=500, reason="Internal Server Error")

    monkeypatch.setattr(api_client.rest_client, "request", fake_request)

    result = order_api_instance.order_cancelling(order_id="12345", isVerify=False)

    assert "error" in result


def test_cover_order_cancelling_success(api_client, requests_mock):
    """Test successful cover order cancellation"""
    api_client.configuration.serverId = "test_server"
    order_api_instance = OrderAPI(api_client)
    url = api_client.configuration.get_url_details("cancel_cover_order")
    mock_response = {"stat": "Ok", "result": "cancelled"}
    requests_mock.post(url, json=mock_response)

    result = order_api_instance.cover_order_cancelling(order_id="12345", isVerify=False)

    assert result["stat"] == "Ok"


def test_cover_order_cancelling_with_verification(api_client, requests_mock):
    """Test cover order cancellation with verification"""
    api_client.configuration.serverId = "test_server"
    order_api_instance = OrderAPI(api_client)
    order_book_url = api_client.configuration.get_url_details("order_book")
    cancel_url = api_client.configuration.get_url_details("cancel_cover_order")

    order_book_response = {
        "data": [
            {"nOrdNo": "12345", "ordSt": "pending", "rejRsn": ""},
        ]
    }
    cancel_response = {"stat": "Ok", "result": "cancelled"}

    requests_mock.get(order_book_url, json=order_book_response)
    requests_mock.post(cancel_url, json=cancel_response)

    result = order_api_instance.cover_order_cancelling(order_id="12345", isVerify=True)

    assert result["stat"] == "Ok"


def test_cover_order_cancelling_verification_traded(api_client, requests_mock):
    """Test cover order cancellation - order is traded"""
    api_client.configuration.serverId = "test_server"
    order_api_instance = OrderAPI(api_client)
    url = api_client.configuration.get_url_details("order_book")

    order_book_response = {
        "data": [
            {"nOrdNo": "12345", "ordSt": "traded", "rejRsn": ""},
        ]
    }

    requests_mock.get(url, json=order_book_response)

    result = order_api_instance.cover_order_cancelling(order_id="12345", isVerify=True)

    assert "Error" in result
    assert result["Error"] == "The Given Order Status is traded"


def test_cover_order_cancelling_api_exception(api_client, monkeypatch):
    """Test cover order cancellation with API exception"""
    from neo_api_client.exceptions import ApiException

    api_client.configuration.serverId = "test_server"
    order_api_instance = OrderAPI(api_client)

    def fake_request(*args, **kwargs):
        raise ApiException(status=400, reason="Bad Request")

    monkeypatch.setattr(api_client.rest_client, "request", fake_request)

    result = order_api_instance.cover_order_cancelling(order_id="12345", isVerify=False)

    assert "error" in result


def test_bracket_order_cancelling_success(api_client, requests_mock):
    """Test successful bracket order cancellation"""
    api_client.configuration.serverId = "test_server"
    order_api_instance = OrderAPI(api_client)
    url = api_client.configuration.get_url_details("cancel_bracket_order")
    mock_response = {"stat": "Ok", "result": "cancelled"}
    requests_mock.post(url, json=mock_response)

    result = order_api_instance.bracket_order_cancelling(order_id="12345", isVerify=False)

    assert result["stat"] == "Ok"


def test_bracket_order_cancelling_with_verification(api_client, requests_mock):
    """Test bracket order cancellation with verification"""
    api_client.configuration.serverId = "test_server"
    order_api_instance = OrderAPI(api_client)
    order_book_url = api_client.configuration.get_url_details("order_book")
    cancel_url = api_client.configuration.get_url_details("cancel_bracket_order")

    order_book_response = {
        "data": [
            {"nOrdNo": "12345", "ordSt": "open", "rejRsn": ""},
        ]
    }
    cancel_response = {"stat": "Ok", "result": "cancelled"}

    requests_mock.get(order_book_url, json=order_book_response)
    requests_mock.post(cancel_url, json=cancel_response)

    result = order_api_instance.bracket_order_cancelling(order_id="12345", isVerify=True)

    assert result["stat"] == "Ok"


def test_bracket_order_cancelling_verification_rejected(api_client, requests_mock):
    """Test bracket order cancellation - order is rejected"""
    api_client.configuration.serverId = "test_server"
    order_api_instance = OrderAPI(api_client)
    url = api_client.configuration.get_url_details("order_book")

    order_book_response = {
        "data": [
            {
                "nOrdNo": "12345",
                "ordSt": "rejected",
                "rejRsn": "Invalid price",
            },
        ]
    }

    requests_mock.get(url, json=order_book_response)

    result = order_api_instance.bracket_order_cancelling(order_id="12345", isVerify=True)

    assert "Error" in result
    assert result["Reason"] == "Invalid price"


def test_bracket_order_cancelling_api_exception(api_client, monkeypatch):
    """Test bracket order cancellation with API exception"""
    from neo_api_client.exceptions import ApiException

    api_client.configuration.serverId = "test_server"
    order_api_instance = OrderAPI(api_client)

    def fake_request(*args, **kwargs):
        raise ApiException(status=500, reason="Internal Server Error")

    monkeypatch.setattr(api_client.rest_client, "request", fake_request)

    result = order_api_instance.bracket_order_cancelling(order_id="12345", isVerify=False)

    assert "error" in result


def test_order_cancelling_with_whitespace(api_client, requests_mock):
    """Test order cancellation with order_id containing whitespace"""
    api_client.configuration.serverId = "test_server"
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
