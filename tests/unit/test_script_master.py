from neo_api_client.services.scrip_master import ScripMasterAPI

URL = "https://test-api.kotak.com/script-details/1.0/masterscrip/file-paths"


def test_scrip_master_all(requests_mock, api_client):
    requests_mock.get(
        URL,
        json={
            "data": {
                "filesPaths": [
                    "nse_cm.csv",
                    "bse_cm.csv",
                ]
            }
        },
    )

    response = ScripMasterAPI(api_client).scrip_master_init()

    assert "filesPaths" in response
    assert len(response["filesPaths"]) == 2


def test_scrip_master_exchange_filter(requests_mock, api_client):
    requests_mock.get(
        URL,
        json={
            "data": {
                "filesPaths": [
                    "nse_cm.csv",
                    "bse_cm.csv",
                ]
            }
        },
    )

    response = ScripMasterAPI(api_client).scrip_master_init("nse_cm")

    assert response == "nse_cm.csv"


def test_scrip_master_exchange_not_found(requests_mock, api_client):
    requests_mock.get(
        URL,
        json={
            "data": {
                "filesPaths": [
                    "bse_cm.csv",
                ]
            }
        },
    )

    response = ScripMasterAPI(api_client).scrip_master_init("nse_cm")

    assert response == {"Error": "Exchange segment not found"}


def test_scrip_master_http_error(requests_mock, api_client):
    requests_mock.get(
        URL,
        status_code=500,
        json={"error": "internal error"},
    )

    response = ScripMasterAPI(api_client).scrip_master_init()

    assert response == {"error": "internal error"}


def test_scrip_master_api_exception_handled(api_client, monkeypatch):
    """An ApiException from the request is caught and returned (line 37)."""
    from neo_api_client.exceptions import ApiException

    api = ScripMasterAPI(api_client)

    def boom(*args, **kwargs):
        raise ApiException(status=500, reason="boom")

    monkeypatch.setattr(api.rest_client, "request", boom)

    response = api.scrip_master_init()
    assert "error" in response
