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


def test_order_report_request_exception(api_client, monkeypatch):
    """An HTTP error in ordered_books() is caught and logged (returns None)."""
    import httpx

    import neo_api_client.services.order_report as order_report_module

    def boom(*args, **kwargs):
        raise httpx.HTTPError("network down")

    monkeypatch.setattr(api_client.rest_client, "request", boom)

    logged = {}
    orig_error = order_report_module.logger.error

    def capture_error(event, **kwargs):
        logged["event"] = event
        logged.update(kwargs)
        return orig_error(event, **kwargs)

    monkeypatch.setattr(order_report_module.logger, "error", capture_error)

    result = OrderReportAPI(api_client).ordered_books()

    assert result is None
    assert logged["event"] == "order_report_request_failed"
    assert "network down" in logged["error"]


def test_order_report_does_not_send_neo_fin_key(api_client, requests_mock):
    url = api_client.configuration.get_url_details("order_book")
    requests_mock.get(url, json={"data": []}, status_code=200)

    OrderReportAPI(api_client).ordered_books()

    assert "neo-fin-key" not in requests_mock.last_request.headers


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
    assert "neo-fin-key" not in requests_mock.last_request.headers


def test_order_report_by_id_request_exception(api_client, monkeypatch):
    """An HTTP error in the by-id path is caught and logged (returns None)."""
    import httpx

    import neo_api_client.services.order_report as order_report_module

    def boom(*args, **kwargs):
        raise httpx.HTTPError("network down")

    monkeypatch.setattr(api_client.rest_client, "request", boom)

    logged = {}
    orig_error = order_report_module.logger.error

    def capture_error(event, **kwargs):
        logged["event"] = event
        logged.update(kwargs)
        return orig_error(event, **kwargs)

    monkeypatch.setattr(order_report_module.logger, "error", capture_error)

    result = OrderReportAPI(api_client).ordered_book_by_id(order_id="123")

    assert result is None
    assert logged["event"] == "order_report_request_failed"
    assert "network down" in logged["error"]
