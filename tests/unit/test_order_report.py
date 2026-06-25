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
