import httpx

from neo_api_client.services.trade_report import TradeReportAPI


def test_trade_report_success(api_client, requests_mock):
    payload = {
        "stat": "Ok",
        "data": [{"nOrdNo": "111"}, {"nOrdNo": "123456"}],
    }

    requests_mock.get(
        "https://test-api.kotak.com/quick/user/trades",
        json=payload,
    )

    response = TradeReportAPI(api_client).trading_report()

    assert response == payload
    assert "neo-fin-key" not in requests_mock.last_request.headers


def test_trade_report_http_error_wrapped(api_client, monkeypatch):
    """An httpx transport error is caught and returned as an Error dict."""

    def boom(*args, **kwargs):
        raise httpx.HTTPError("network down")

    monkeypatch.setattr(api_client.rest_client, "request", boom)

    response = TradeReportAPI(api_client).trading_report()

    assert "Error" in response
