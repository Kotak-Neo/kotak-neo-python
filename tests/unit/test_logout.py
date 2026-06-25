from neo_api_client.exceptions import ApiException
from neo_api_client.services.logout import LogoutAPI


def test_logout(requests_mock, api_client):
    api_client.configuration.bearer_token = "dummy-token"

    requests_mock.post(
        "https://test-api.kotak.com/apim/login/2.0/logout",
        json={"stat": "Ok"},
    )

    response = LogoutAPI(api_client).logging_out()

    assert response["stat"] == "Ok"


def test_logout_exception(api_client, monkeypatch):
    def fake_request(*args, **kwargs):
        raise ApiException(status=500, reason="boom")

    monkeypatch.setattr(
        api_client.rest_client,
        "request",
        fake_request,
    )

    response = LogoutAPI(api_client).logging_out()

    assert "error" in response
