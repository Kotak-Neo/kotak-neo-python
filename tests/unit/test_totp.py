"""Unit tests for TOTP authentication service."""

from neo_api_client.services.totp import TotpAPI


def test_totp_api_init(api_client):
    """Test TotpAPI initialization."""
    totp_api = TotpAPI(api_client)
    assert totp_api.api_client == api_client
    assert totp_api.rest_client == api_client.rest_client
    assert totp_api.totp_session is None


def test_totp_login_success(api_client, requests_mock):
    """Test successful TOTP login."""
    login_url = api_client.configuration.get_domain(session_init=True) + "/login/1.0/tradeApiLogin"

    requests_mock.post(
        login_url,
        json={
            "data": {
                "token": "view_token_123",
                "sid": "view_sid_456",
                "rid": "view_rid_789",
            }
        },
        status_code=200,
    )

    totp_api = TotpAPI(api_client)
    result = totp_api.totp_login(
        mobile_number="+919999999999",
        ucc="TESTUSER",
        totp="123456",
    )

    assert result["data"]["token"] == "view_token_123"
    assert result["data"]["sid"] == "view_sid_456"
    assert api_client.configuration.view_token == "view_token_123"
    assert api_client.configuration.sid == "view_sid_456"


def test_totp_validate_success(api_client, requests_mock):
    """Test successful TOTP validation."""
    # First login to set view_token and sid
    api_client.configuration.view_token = "view_token_123"
    api_client.configuration.sid = "view_sid_456"

    validate_url = (
        api_client.configuration.get_domain(session_init=True) + "/login/1.0/tradeApiValidate"
    )

    requests_mock.post(
        validate_url,
        json={
            "data": {
                "token": "edit_token_123",
                "sid": "edit_sid_456",
                "rid": "edit_rid_789",
                "dataCenter": "DC1",
                "baseUrl": "https://test.com",
            }
        },
        status_code=200,
    )

    totp_api = TotpAPI(api_client)
    result = totp_api.totp_validate(mpin="654321")

    assert result["data"]["token"] == "edit_token_123"
    assert result["data"]["sid"] == "edit_sid_456"
    assert api_client.configuration.edit_token == "edit_token_123"
    assert api_client.configuration.edit_sid == "edit_sid_456"
    assert api_client.configuration.data_center == "DC1"


def test_totp_login_with_none_values(api_client, requests_mock):
    """Test TOTP login accepts None values without raising errors."""
    login_url = api_client.configuration.get_domain(session_init=True) + "/login/1.0/tradeApiLogin"

    requests_mock.post(
        login_url,
        json={"data": {"token": "test", "sid": "test"}},
        status_code=200,
    )

    totp_api = TotpAPI(api_client)
    # Should not raise TypeError
    result = totp_api.totp_login(mobile_number=None, ucc=None, totp=None)

    assert "data" in result


def test_totp_validate_with_none_mpin(api_client, requests_mock):
    """Test TOTP validate accepts None mpin without raising errors."""
    api_client.configuration.view_token = "view_token"
    api_client.configuration.sid = "sid"

    validate_url = (
        api_client.configuration.get_domain(session_init=True) + "/login/1.0/tradeApiValidate"
    )

    requests_mock.post(
        validate_url,
        json={"data": {"token": "edit_token", "sid": "edit_sid", "rid": "rid"}},
        status_code=200,
    )

    totp_api = TotpAPI(api_client)
    # Should not raise TypeError
    result = totp_api.totp_validate(mpin=None)

    assert "data" in result


def test_totp_login_invalid_json_response(api_client, requests_mock):
    """Test TOTP login with invalid JSON response."""
    login_url = api_client.configuration.get_domain(session_init=True) + "/login/1.0/tradeApiLogin"

    requests_mock.post(login_url, text="Invalid JSON", status_code=200)

    totp_api = TotpAPI(api_client)
    result = totp_api.totp_login(
        mobile_number="+919999999999",
        ucc="TESTUSER",
        totp="123456",
    )

    assert "Error" in result
    assert "Unexpected response format" in result["Error"]


def test_totp_validate_invalid_json_response(api_client, requests_mock):
    """Test TOTP validate with invalid JSON response."""
    api_client.configuration.view_token = "view_token"
    api_client.configuration.sid = "sid"

    validate_url = (
        api_client.configuration.get_domain(session_init=True) + "/login/1.0/tradeApiValidate"
    )

    requests_mock.post(validate_url, text="Invalid JSON", status_code=200)

    totp_api = TotpAPI(api_client)
    result = totp_api.totp_validate(mpin="123456")

    assert "Error" in result
    assert "Unexpected response format" in result["Error"]


def test_totp_login_error_status(api_client, requests_mock):
    """Test TOTP login with error status code."""
    login_url = api_client.configuration.get_domain(session_init=True) + "/login/1.0/tradeApiLogin"

    requests_mock.post(
        login_url,
        json={"stat": "Not_Ok", "message": "Invalid credentials"},
        status_code=401,
    )

    totp_api = TotpAPI(api_client)
    result = totp_api.totp_login(
        mobile_number="+919999999999",
        ucc="TESTUSER",
        totp="000000",
    )

    assert result["stat"] == "Not_Ok"
    # Configuration should not be updated on error
    assert api_client.configuration.view_token is None
