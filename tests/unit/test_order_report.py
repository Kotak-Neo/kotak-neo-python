from neo_api_client.services.order_report import OrderReportAPI


def test_order_report(api_client, requests_mock):
    url = api_client.configuration.get_url_details("order_book")

    requests_mock.get(
        url,
        json={"data": []},
        status_code=200,
    )

    response = OrderReportAPI(api_client).ordered_books()

    assert response["data"] == []


def test_order_report_sends_neo_fin_key(api_client, requests_mock):
    url = api_client.configuration.get_url_details("order_book")
    requests_mock.get(url, json={"data": []}, status_code=200)

    OrderReportAPI(api_client).ordered_books()

    assert requests_mock.last_request.headers["neo-fin-key"] == "neotradeapi"


def test_order_report_by_id(api_client, requests_mock):
    order_id = "250720000007242"
    url = f"{api_client.configuration.get_url_details('order_book')}/{order_id}"

    requests_mock.get(
        url,
        json={"stat": "Ok", "stCode": 200, "data": [{"nOrdNo": order_id, "ordSt": "rejected"}]},
        status_code=200,
    )

    response = OrderReportAPI(api_client).ordered_book_by_id(order_id=order_id)

    assert response["data"][0]["nOrdNo"] == order_id
    assert requests_mock.last_request.url.endswith(f"/orders/{order_id}")
    assert requests_mock.last_request.headers["neo-fin-key"] == "neotradeapi"


def test_order_report_by_id_request_exception(api_client, monkeypatch, capsys):
    """A RequestException in the by-id path is caught and logged (returns None)."""
    import requests

    def boom(*args, **kwargs):
        raise requests.exceptions.RequestException("network down")

    monkeypatch.setattr(api_client.rest_client, "request", boom)

    result = OrderReportAPI(api_client).ordered_book_by_id(order_id="123")

    assert result is None
    assert "Error occurred" in capsys.readouterr().out
