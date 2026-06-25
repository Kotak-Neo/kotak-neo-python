from neo_api_client.services.trade_report import TradeReportAPI


def test_trade_report_with_order_id(api_client, requests_mock):
    requests_mock.get(
        "https://test-api.kotak.com/quick/user/trades",
        json={
            "stat": "Ok",
            "stCode": 200,
            "data": [
                {"nOrdNo": "111"},
                {"nOrdNo": "123456"},
            ],
        },
    )

    response = TradeReportAPI(api_client).trading_report("123456")

    assert response["stat"] == "Ok"
    assert response["data"]["nOrdNo"] == "123456"


def test_trade_report_no_order_id(api_client, requests_mock):
    payload = {
        "stat": "Ok",
        "data": [{"nOrdNo": "111"}],
    }

    requests_mock.get(
        "https://test-api.kotak.com/quick/user/trades",
        json=payload,
    )

    response = TradeReportAPI(api_client).trading_report(None)

    assert response == payload


def test_trade_report_no_data(api_client, requests_mock):
    requests_mock.get(
        "https://test-api.kotak.com/quick/user/trades",
        json={"message": "empty"},
    )

    response = TradeReportAPI(api_client).trading_report("123")

    assert "Error" in response
