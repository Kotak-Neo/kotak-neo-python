import json

import requests_mock

from neo_api_client.services.login import LoginAPI
from neo_api_client.services.totp import TotpAPI


def test_totp_login(api_client):
    url = api_client.configuration.get_domain(session_init=True) + "/login/1.0/tradeApiLogin"

    with requests_mock.Mocker() as mocker:
        mocker.post(
            url,
            json={
                "data": {
                    "token": "abc123",
                    "sid": "xyz456",
                }
            },
            status_code=200,
        )

        response = TotpAPI(api_client).totp_login(
            mobile_number="9999999999",
            ucc="ABC123",
            totp="123456",
        )

        assert response["data"]["token"] == "abc123"
        assert api_client.configuration.view_token == "abc123"


def test_totp_validate(api_client):
    api_client.configuration.sid = "SID123"
    api_client.configuration.view_token = "TOKEN123"

    url = api_client.configuration.get_domain(session_init=True) + "/login/1.0/tradeApiValidate"

    with requests_mock.Mocker() as mocker:
        mocker.post(
            url,
            json={
                "data": {
                    "token": "edittoken",
                    "sid": "editsid",
                    "rid": "rid123",
                    "dataCenter": "dc1",
                    "baseUrl": "https://trade-api.example.com",
                }
            },
            status_code=200,
        )

        response = TotpAPI(api_client).totp_validate(
            mpin="1234",
        )

        assert response["data"]["token"] == "edittoken"
        assert api_client.configuration.base_url == ("https://trade-api.example.com")


def test_session_init_success(requests_mock, api_client):
    api_client.configuration.base64_token = "test-base64-token"

    url = api_client.configuration.get_domain(session_init=True) + "oauth2/token"

    requests_mock.post(
        url,
        text=json.dumps({"access_token": "bearer123"}),
        status_code=200,
    )

    response = LoginAPI(api_client).session_init()

    assert response["access_token"] == "bearer123"
    assert api_client.configuration.bearer_token == "bearer123"


def test_session_init_failure(requests_mock, api_client):
    api_client.configuration.base64_token = "test-base64-token"

    url = api_client.configuration.get_domain(session_init=True) + "oauth2/token"

    requests_mock.post(
        url,
        text="Internal Server Error",
        status_code=500,
    )

    response = LoginAPI(api_client).session_init()

    response_json = json.loads(response)

    assert response_json["data"]["Code"] == 500
    assert "Error occurred to initialise the session" in response_json["data"]["Message"]
