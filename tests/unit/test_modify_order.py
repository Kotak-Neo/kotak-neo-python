from neo_api_client.services.modify_order import ModifyOrder


def test_quick_modification_success(api_client, requests_mock):
    """Test successful quick order modification"""
    modify_order_api = ModifyOrder(api_client)
    url = api_client.configuration.get_url_details("modify_order")
    mock_response = {"stat": "Ok", "nOrdNo": "12345"}
    requests_mock.post(url, json=mock_response)

    result = modify_order_api.quick_modification(
        order_id="12345",
        price="105.00",
        order_type="L",
        quantity="15",
        validity="DAY",
        instrument_token="11536",
        exchange_segment="nse_cm",
        product="CNC",
        trading_symbol="RELIANCE-EQ",
        transaction_type="B",
        trigger_price="104.00",
        dd="NA",
        market_protection="0",
        disclosed_quantity="5",
        filled_quantity="0",
        amo="NO",
    )

    assert result["stat"] == "Ok"
    assert result["nOrdNo"] == "12345"


def test_quick_modification_api_exception(api_client, monkeypatch):
    """Test quick modification with API exception"""
    from neo_api_client.exceptions import ApiException

    modify_order_api = ModifyOrder(api_client)

    def fake_request(*args, **kwargs):
        raise ApiException(status=400, reason="Bad Request")

    monkeypatch.setattr(api_client.rest_client, "request", fake_request)

    result = modify_order_api.quick_modification(
        order_id="12345",
        price="105.00",
        order_type="L",
        quantity="15",
        validity="DAY",
        instrument_token="11536",
        exchange_segment="nse_cm",
        product="CNC",
        trading_symbol="RELIANCE-EQ",
        transaction_type="B",
        trigger_price="104.00",
        dd="NA",
        market_protection="0",
        disclosed_quantity="5",
        filled_quantity="0",
        amo="NO",
    )

    assert "error" in result


def test_modification_with_orderid_success(api_client, requests_mock):
    """Test successful modification with order ID lookup"""
    modify_order_api = ModifyOrder(api_client)
    order_book_url = api_client.configuration.get_url_details("order_book")
    modify_url = api_client.configuration.get_url_details("modify_order")

    order_book_response = {
        "data": [
            {
                "nOrdNo": "12345",
                "ordSt": "pending",
                "rejRsn": "",
                "trdSym": "RELIANCE-EQ",
                "tok": "11536",
                "prod": "CNC",
                "trnsTp": "B",
                "exSeg": "nse_cm",
                "trgPrc": "100.00",
            }
        ]
    }
    modify_response = {"stat": "Ok", "nOrdNo": "12345"}

    requests_mock.get(order_book_url, json=order_book_response)
    requests_mock.post(modify_url, json=modify_response)

    result = modify_order_api.modification_with_orderid(
        order_id="12345",
        price="105.00",
        order_type="L",
        quantity="15",
        validity="DAY",
        instrument_token=None,
        exchange_segment=None,
        product=None,
        trading_symbol=None,
        transaction_type=None,
        trigger_price="0",
        dd="NA",
        market_protection="0",
        disclosed_quantity="5",
        filled_quantity="0",
        amo="NO",
    )

    assert result["stat"] == "Ok"


def test_modification_with_orderid_no_data(api_client, requests_mock):
    """Test modification when order book has no data"""
    modify_order_api = ModifyOrder(api_client)
    url = api_client.configuration.get_url_details("order_book")
    order_book_response = {}

    requests_mock.get(url, json=order_book_response)

    result = modify_order_api.modification_with_orderid(
        order_id="12345",
        price="105.00",
        order_type="L",
        quantity="15",
        validity="DAY",
        instrument_token="11536",
        exchange_segment="nse_cm",
        product="CNC",
        trading_symbol="RELIANCE-EQ",
        transaction_type="B",
        trigger_price="104.00",
        dd="NA",
        market_protection="0",
        disclosed_quantity="5",
        filled_quantity="0",
        amo="NO",
    )

    assert "Message" in result
    assert result["Message"] == "There is no Data in the Order Book"


def test_modification_with_orderid_rejected(api_client, requests_mock):
    """Test modification when order is rejected"""
    modify_order_api = ModifyOrder(api_client)
    url = api_client.configuration.get_url_details("order_book")

    order_book_response = {
        "data": [
            {
                "nOrdNo": "12345",
                "ordSt": "rejected",
                "rejRsn": "Insufficient funds",
                "trdSym": "RELIANCE-EQ",
                "tok": "11536",
                "prod": "CNC",
                "trnsTp": "B",
                "exSeg": "nse_cm",
                "trgPrc": "100.00",
            }
        ]
    }

    requests_mock.get(url, json=order_book_response)

    result = modify_order_api.modification_with_orderid(
        order_id="12345",
        price="105.00",
        order_type="L",
        quantity="15",
        validity="DAY",
        instrument_token=None,
        exchange_segment=None,
        product=None,
        trading_symbol=None,
        transaction_type=None,
        trigger_price="104.00",
        dd="NA",
        market_protection="0",
        disclosed_quantity="5",
        filled_quantity="0",
        amo="NO",
    )

    assert "Error" in result
    assert "rejected" in result["Error"]
    assert result["Reason"] == "Insufficient funds"


def test_modification_with_orderid_cancelled(api_client, requests_mock):
    """Test modification when order is cancelled"""
    modify_order_api = ModifyOrder(api_client)
    url = api_client.configuration.get_url_details("order_book")

    order_book_response = {
        "data": [
            {
                "nOrdNo": "12345",
                "ordSt": "cancelled",
                "rejRsn": "User cancelled",
                "trdSym": "RELIANCE-EQ",
                "tok": "11536",
                "prod": "CNC",
                "trnsTp": "B",
                "exSeg": "nse_cm",
                "trgPrc": "100.00",
            }
        ]
    }

    requests_mock.get(url, json=order_book_response)

    result = modify_order_api.modification_with_orderid(
        order_id="12345",
        price="105.00",
        order_type="L",
        quantity="15",
        validity="DAY",
        instrument_token=None,
        exchange_segment=None,
        product=None,
        trading_symbol=None,
        transaction_type=None,
        trigger_price="104.00",
        dd="NA",
        market_protection="0",
        disclosed_quantity="5",
        filled_quantity="0",
        amo="NO",
    )

    assert "Error" in result
    assert "cancelled" in result["Error"]


def test_modification_with_orderid_complete(api_client, requests_mock):
    """Test modification when order is complete"""
    modify_order_api = ModifyOrder(api_client)
    url = api_client.configuration.get_url_details("order_book")

    order_book_response = {
        "data": [
            {
                "nOrdNo": "12345",
                "ordSt": "complete",
                "rejRsn": "",
                "trdSym": "RELIANCE-EQ",
                "tok": "11536",
                "prod": "CNC",
                "trnsTp": "B",
                "exSeg": "nse_cm",
                "trgPrc": "100.00",
            }
        ]
    }

    requests_mock.get(url, json=order_book_response)

    result = modify_order_api.modification_with_orderid(
        order_id="12345",
        price="105.00",
        order_type="L",
        quantity="15",
        validity="DAY",
        instrument_token=None,
        exchange_segment=None,
        product=None,
        trading_symbol=None,
        transaction_type=None,
        trigger_price="104.00",
        dd="NA",
        market_protection="0",
        disclosed_quantity="5",
        filled_quantity="0",
        amo="NO",
    )

    assert "Error" in result
    assert "Traded" in result["Error"]


def test_modification_with_orderid_traded(api_client, requests_mock):
    """Test modification when order is traded"""
    modify_order_api = ModifyOrder(api_client)
    url = api_client.configuration.get_url_details("order_book")

    order_book_response = {
        "data": [
            {
                "nOrdNo": "12345",
                "ordSt": "traded",
                "rejRsn": "",
                "trdSym": "RELIANCE-EQ",
                "tok": "11536",
                "prod": "CNC",
                "trnsTp": "B",
                "exSeg": "nse_cm",
                "trgPrc": "100.00",
            }
        ]
    }

    requests_mock.get(url, json=order_book_response)

    result = modify_order_api.modification_with_orderid(
        order_id="12345",
        price="105.00",
        order_type="L",
        quantity="15",
        validity="DAY",
        instrument_token=None,
        exchange_segment=None,
        product=None,
        trading_symbol=None,
        transaction_type=None,
        trigger_price="104.00",
        dd="NA",
        market_protection="0",
        disclosed_quantity="5",
        filled_quantity="0",
        amo="NO",
    )

    assert "Error" in result
    assert "traded" in result["Error"]


def test_modification_with_orderid_not_matching(api_client, requests_mock):
    """Test modification when order ID doesn't match"""
    modify_order_api = ModifyOrder(api_client)
    url = api_client.configuration.get_url_details("order_book")

    order_book_response = {
        "data": [
            {
                "nOrdNo": "99999",
                "ordSt": "pending",
                "rejRsn": "",
                "trdSym": "RELIANCE-EQ",
                "tok": "11536",
                "prod": "CNC",
                "trnsTp": "B",
                "exSeg": "nse_cm",
                "trgPrc": "100.00",
            }
        ]
    }

    requests_mock.get(url, json=order_book_response)

    result = modify_order_api.modification_with_orderid(
        order_id="12345",
        price="105.00",
        order_type="L",
        quantity="15",
        validity="DAY",
        instrument_token=None,
        exchange_segment=None,
        product=None,
        trading_symbol=None,
        transaction_type=None,
        trigger_price="104.00",
        dd="NA",
        market_protection="0",
        disclosed_quantity="5",
        filled_quantity="0",
        amo="NO",
    )

    assert "Message" in result
    assert "12345" in result["Message"]
    assert "not matching" in result["Message"]


def test_modification_with_orderid_api_exception(api_client, requests_mock, monkeypatch):
    """Test modification with API exception during order modification"""
    from neo_api_client.exceptions import ApiException

    modify_order_api = ModifyOrder(api_client)
    order_book_url = api_client.configuration.get_url_details("order_book")

    order_book_response = {
        "data": [
            {
                "nOrdNo": "12345",
                "ordSt": "pending",
                "rejRsn": "",
                "trdSym": "RELIANCE-EQ",
                "tok": "11536",
                "prod": "CNC",
                "trnsTp": "B",
                "exSeg": "nse_cm",
                "trgPrc": "100.00",
            }
        ]
    }

    requests_mock.get(order_book_url, json=order_book_response)

    # Use monkeypatch to inject exception after order book is retrieved
    original_request = api_client.rest_client.request
    call_count = [0]

    def fake_request(*args, **kwargs):
        call_count[0] += 1
        if call_count[0] > 1:  # First call is for order book, second is for modify
            raise ApiException(status=500, reason="Internal Server Error")
        return original_request(*args, **kwargs)

    monkeypatch.setattr(api_client.rest_client, "request", fake_request)

    result = modify_order_api.modification_with_orderid(
        order_id="12345",
        price="105.00",
        order_type="L",
        quantity="15",
        validity="DAY",
        instrument_token=None,
        exchange_segment=None,
        product=None,
        trading_symbol=None,
        transaction_type=None,
        trigger_price="0",
        dd="NA",
        market_protection="0",
        disclosed_quantity="5",
        filled_quantity="0",
        amo="NO",
    )

    assert "error" in result


def test_modification_with_provided_values(api_client, requests_mock):
    """Test modification with all values provided (not using order book values)"""
    modify_order_api = ModifyOrder(api_client)
    order_book_url = api_client.configuration.get_url_details("order_book")
    modify_url = api_client.configuration.get_url_details("modify_order")

    order_book_response = {
        "data": [
            {
                "nOrdNo": "12345",
                "ordSt": "pending",
                "rejRsn": "",
                "trdSym": "TCS-EQ",
                "tok": "99999",
                "prod": "MIS",
                "trnsTp": "S",
                "exSeg": "bse_cm",
                "trgPrc": "50.00",
            }
        ]
    }
    modify_response = {"stat": "Ok", "nOrdNo": "12345"}

    requests_mock.get(order_book_url, json=order_book_response)
    requests_mock.post(modify_url, json=modify_response)

    result = modify_order_api.modification_with_orderid(
        order_id="12345",
        price="105.00",
        order_type="L",
        quantity="15",
        validity="DAY",
        instrument_token="11536",
        exchange_segment="nse_cm",
        product="CNC",
        trading_symbol="RELIANCE-EQ",
        transaction_type="B",
        trigger_price="104.00",
        dd="NA",
        market_protection="0",
        disclosed_quantity="5",
        filled_quantity="0",
        amo="NO",
    )

    assert result["stat"] == "Ok"
