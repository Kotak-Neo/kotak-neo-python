from neo_api_client.exceptions import ApiException
from neo_api_client.services.limits import LimitsAPI


def test_limits(requests_mock, api_client):
    requests_mock.post(
        "https://test-api.kotak.com/quick/user/limits",
        json={"stat": "Ok"},
    )

    response = LimitsAPI(api_client).limit_init()

    assert response["stat"] == "Ok"


def test_limits_api_exception(api_client, monkeypatch):
    def mock_request(*args, **kwargs):
        raise ApiException(status=500, reason="Test Error")

    monkeypatch.setattr(
        api_client.rest_client,
        "request",
        mock_request,
    )

    response = LimitsAPI(api_client).limit_init()

    assert "error" in response
    assert isinstance(response["error"], ApiException)
