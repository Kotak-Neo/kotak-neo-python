import pytest

from neo_api_client.exceptions import ApiException
from neo_api_client.services.margin import MarginAPI


def test_margin(api_client, requests_mock):
    requests_mock.post(
        "https://test-api.kotak.com/quick/user/check-margin",
        text='{"stat":"Ok"}',
    )

    response = MarginAPI(api_client).margin_init(
        exchange_segment="nse_cm",
        price="100",
        order_type="MKT",
        product="MIS",
        quantity="1",
        instrument_token="12345",
        transaction_type="B",
        trigger_price="0",
        broker_name="KOTAK",
        branch_id="1",
        stop_loss_type="ABS",
        stop_loss_value="0",
        square_off_type="ABS",
        square_off_value="0",
        trailing_stop_loss="N",
        trailing_sl_value="0",
    )

    assert response["data"]["stat"] == "Ok"


def test_margin_api_exception(api_client, monkeypatch):
    def mock_request(*args, **kwargs):
        raise ApiException(status=500, reason="Test Error")

    monkeypatch.setattr(
        api_client.rest_client,
        "request",
        mock_request,
    )

    response = MarginAPI(api_client).margin_init(
        exchange_segment="nse_cm",
        price="100",
        order_type="L",
        product="CNC",
        quantity="1",
        instrument_token="12345",
        transaction_type="B",
        trigger_price="0",
        broker_name="KOTAK",
        branch_id="1",
        stop_loss_type="ABS",
        stop_loss_value="0",
        square_off_type="ABS",
        square_off_value="0",
        trailing_stop_loss="N",
        trailing_sl_value="0",
    )

    assert "error" in response
    assert isinstance(response["error"], ApiException)


def test_margin_cnc_product(api_client, requests_mock):
    """Test margin calculation for CNC product."""
    requests_mock.post(
        "https://test-api.kotak.com/quick/user/check-margin",
        text='{"stat":"Ok","data":{"margin":"10000.50"}}',
    )

    response = MarginAPI(api_client).margin_init(
        exchange_segment="nse_cm",
        price="1500",
        order_type="L",
        product="CNC",
        quantity="10",
        instrument_token="1333",
        transaction_type="B",
        trigger_price="0",
        broker_name="KOTAK",
        branch_id="1",
        stop_loss_type="ABS",
        stop_loss_value="0",
        square_off_type="ABS",
        square_off_value="0",
        trailing_stop_loss="N",
        trailing_sl_value="0",
    )

    assert response["data"]["stat"] == "Ok"
    assert "margin" in response["data"]["data"]


def test_margin_mis_product(api_client, requests_mock):
    """Test margin calculation for MIS product."""
    requests_mock.post(
        "https://test-api.kotak.com/quick/user/check-margin",
        text='{"stat":"Ok","data":{"margin":"5000.25"}}',
    )

    response = MarginAPI(api_client).margin_init(
        exchange_segment="nse_cm",
        price="1500",
        order_type="L",
        product="MIS",
        quantity="10",
        instrument_token="1333",
        transaction_type="B",
        trigger_price="0",
        broker_name="KOTAK",
        branch_id="1",
        stop_loss_type="ABS",
        stop_loss_value="0",
        square_off_type="ABS",
        square_off_value="0",
        trailing_stop_loss="N",
        trailing_sl_value="0",
    )

    assert response["data"]["stat"] == "Ok"


def test_margin_sell_order(api_client, requests_mock):
    """Test margin calculation for sell order."""
    requests_mock.post(
        "https://test-api.kotak.com/quick/user/check-margin",
        text='{"stat":"Ok","data":{"margin":"2500.00"}}',
    )

    response = MarginAPI(api_client).margin_init(
        exchange_segment="nse_cm",
        price="1500",
        order_type="L",
        product="CNC",
        quantity="5",
        instrument_token="1333",
        transaction_type="S",
        trigger_price="0",
        broker_name="KOTAK",
        branch_id="1",
        stop_loss_type="ABS",
        stop_loss_value="0",
        square_off_type="ABS",
        square_off_value="0",
        trailing_stop_loss="N",
        trailing_sl_value="0",
    )

    assert response["data"]["stat"] == "Ok"


def test_margin_nse_fo(api_client, requests_mock):
    """Test margin calculation for NSE F&O."""
    requests_mock.post(
        "https://test-api.kotak.com/quick/user/check-margin",
        text='{"stat":"Ok","data":{"margin":"50000.00"}}',
    )

    response = MarginAPI(api_client).margin_init(
        exchange_segment="nse_fo",
        price="100",
        order_type="L",
        product="NRML",
        quantity="50",
        instrument_token="12345",
        transaction_type="B",
        trigger_price="0",
        broker_name="KOTAK",
        branch_id="1",
        stop_loss_type="ABS",
        stop_loss_value="0",
        square_off_type="ABS",
        square_off_value="0",
        trailing_stop_loss="N",
        trailing_sl_value="0",
    )

    assert response["data"]["stat"] == "Ok"


def test_margin_with_stop_loss(api_client, requests_mock):
    """Test margin calculation with stop loss."""
    requests_mock.post(
        "https://test-api.kotak.com/quick/user/check-margin",
        text='{"stat":"Ok","data":{"margin":"3000.00"}}',
    )

    response = MarginAPI(api_client).margin_init(
        exchange_segment="nse_cm",
        price="1500",
        order_type="L",
        product="MIS",
        quantity="10",
        instrument_token="1333",
        transaction_type="B",
        trigger_price="0",
        broker_name="KOTAK",
        branch_id="1",
        stop_loss_type="ABS",
        stop_loss_value="50",
        square_off_type="ABS",
        square_off_value="0",
        trailing_stop_loss="N",
        trailing_sl_value="0",
    )

    assert response["data"]["stat"] == "Ok"


def test_margin_with_trailing_sl(api_client, requests_mock):
    """Test margin calculation with trailing stop loss."""
    requests_mock.post(
        "https://test-api.kotak.com/quick/user/check-margin",
        text='{"stat":"Ok","data":{"margin":"3500.00"}}',
    )

    response = MarginAPI(api_client).margin_init(
        exchange_segment="nse_cm",
        price="1500",
        order_type="L",
        product="MIS",
        quantity="10",
        instrument_token="1333",
        transaction_type="B",
        trigger_price="0",
        broker_name="KOTAK",
        branch_id="1",
        stop_loss_type="ABS",
        stop_loss_value="0",
        square_off_type="ABS",
        square_off_value="0",
        trailing_stop_loss="Y",
        trailing_sl_value="20",
    )

    assert response["data"]["stat"] == "Ok"


def test_margin_insufficient_funds(api_client, requests_mock):
    """Test margin response when funds are insufficient."""
    requests_mock.post(
        "https://test-api.kotak.com/quick/user/check-margin",
        text='{"stat":"Not_Ok","message":"Insufficient funds"}',
    )

    response = MarginAPI(api_client).margin_init(
        exchange_segment="nse_cm",
        price="10000",
        order_type="L",
        product="CNC",
        quantity="1000",
        instrument_token="1333",
        transaction_type="B",
        trigger_price="0",
        broker_name="KOTAK",
        branch_id="1",
        stop_loss_type="ABS",
        stop_loss_value="0",
        square_off_type="ABS",
        square_off_value="0",
        trailing_stop_loss="N",
        trailing_sl_value="0",
    )

    assert response["data"]["stat"] == "Not_Ok"


def test_margin_invalid_instrument(api_client, requests_mock):
    """Test margin with invalid instrument token."""
    requests_mock.post(
        "https://test-api.kotak.com/quick/user/check-margin",
        text='{"stat":"Not_Ok","message":"Invalid instrument token"}',
    )

    response = MarginAPI(api_client).margin_init(
        exchange_segment="nse_cm",
        price="100",
        order_type="L",
        product="CNC",
        quantity="1",
        instrument_token="999999",
        transaction_type="B",
        trigger_price="0",
        broker_name="KOTAK",
        branch_id="1",
        stop_loss_type="ABS",
        stop_loss_value="0",
        square_off_type="ABS",
        square_off_value="0",
        trailing_stop_loss="N",
        trailing_sl_value="0",
    )

    assert response["data"]["stat"] == "Not_Ok"


def test_margin_missing_required_params(api_client):
    """Test margin with missing required parameters."""
    with pytest.raises(TypeError):
        MarginAPI(api_client).margin_init(
            exchange_segment="nse_cm",
            # Missing other required params
        )
