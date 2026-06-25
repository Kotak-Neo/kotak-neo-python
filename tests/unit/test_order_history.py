from neo_api_client.exceptions import ApiException
from neo_api_client.services.order_history import OrderHistoryAPI


def test_order_history(api_client, requests_mock):
    requests_mock.post(
        "https://test-api.kotak.com/quick/order/history",
        text='{"stat":"Ok"}',
    )

    response = OrderHistoryAPI(api_client).ordered_history("123")

    assert response["data"]["stat"] == "Ok"


def test_order_history_exception(api_client, monkeypatch):
    def mock_request(*args, **kwargs):
        raise ApiException("error")

    api_client.rest_client.request = mock_request

    response = OrderHistoryAPI(api_client).ordered_history("123")

    assert "error" in response
