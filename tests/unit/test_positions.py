import httpx

from neo_api_client.services.positions import PositionsAPI


def test_positions(api_client, requests_mock):
    url = api_client.configuration.get_url_details("positions")

    requests_mock.get(
        url,
        json={"data": []},
        status_code=200,
    )

    response = PositionsAPI(api_client).position_init()

    assert response["data"] == []


def test_positions_request_exception(api_client, monkeypatch):
    import neo_api_client.services.positions as positions_module

    def mock_request(*args, **kwargs):
        raise httpx.HTTPError("Connection error")

    monkeypatch.setattr(
        api_client.rest_client,
        "request",
        mock_request,
    )

    logged = {}
    orig_error = positions_module.logger.error

    def capture_error(event, **kwargs):
        logged["event"] = event
        logged.update(kwargs)
        return orig_error(event, **kwargs)

    monkeypatch.setattr(positions_module.logger, "error", capture_error)

    response = PositionsAPI(api_client).position_init()

    assert response is None
    assert logged["event"] == "positions_request_failed"
    assert "Connection error" in logged["error"]
