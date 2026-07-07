"""Unit tests for the get-client-ip endpoint."""

from neo_api_client import NeoAPI
from neo_api_client.services.client_ip import ClientIpAPI

_IP_RESPONSE = {
    "data": [{"ip": "165.85.130.248", "time": "2026-07-07 12:07:34.440"}],
    "stCode": 1000,
    "status": "success",
}


def _authed_client():
    client = NeoAPI(environment="prod", consumer_key="consumer-key-123")
    client.configuration.edit_token = "trade_token_123"
    client.configuration.edit_sid = "sid_123"
    return client


def _ip_url(client):
    from neo_api_client.settings import PROD_URL

    return client.configuration.get_domain(session_init=True) + "/" + PROD_URL["get_client_ip"]


def test_whatsmyip_success(requests_mock):
    client = _authed_client()
    requests_mock.get(_ip_url(client), json=_IP_RESPONSE, status_code=200)

    result = client.whatsmyip()

    assert result["status"] == "success"
    assert result["stCode"] == 1000
    assert result["data"][0]["ip"] == "165.85.130.248"


def test_whatsmyip_sends_expected_headers(requests_mock):
    client = _authed_client()
    requests_mock.get(_ip_url(client), json=_IP_RESPONSE, status_code=200)

    client.whatsmyip()

    headers = requests_mock.last_request.headers
    assert headers["Auth"] == "trade_token_123"
    assert headers["Sid"] == "sid_123"
    assert headers["Authorization"] == "consumer-key-123"


def test_whatsmyip_uses_session_login_url(requests_mock):
    """The endpoint must hit login/1.0/get-client-ip on the session host."""
    client = _authed_client()
    requests_mock.get(_ip_url(client), json=_IP_RESPONSE, status_code=200)

    client.whatsmyip()

    assert requests_mock.last_request.url.endswith("/login/1.0/get-client-ip")


def test_whatsmyip_without_2fa():
    client = NeoAPI(environment="prod", consumer_key="consumer-key-123")

    result = client.whatsmyip()

    assert "Error Message" in result
    assert "2fa" in result["Error Message"]


def test_whatsmyip_api_exception(monkeypatch):
    from neo_api_client.exceptions import ApiException

    client = _authed_client()
    service = ClientIpAPI(client.api_client)

    def boom(*args, **kwargs):
        raise ApiException(status=500, reason="Server Error")

    monkeypatch.setattr(service.rest_client, "request", boom)

    result = service.whatsmyip()
    assert "error" in result


def test_whatsmyip_non_json_response(requests_mock):
    client = _authed_client()
    requests_mock.get(_ip_url(client), text="<html>not json</html>", status_code=200)

    result = client.whatsmyip()
    assert "Error" in result
