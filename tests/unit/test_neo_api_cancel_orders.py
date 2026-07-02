"""Unit tests for cancel order methods in NeoAPI."""

import pytest

from neo_api_client import NeoAPI


@pytest.fixture
def authenticated_client():
    """Create an authenticated NeoAPI client."""
    client = NeoAPI(environment="prod", consumer_key="test_key")
    client.configuration.edit_token = "edit_token_123"
    client.configuration.edit_sid = "edit_sid_123"
    client.configuration.view_token = "view_token_123"
    client.configuration.sid = "sid_123"
    client.configuration.base_url = "https://gw-napi.kotaksecurities.com"
    return client


def test_cancel_order_success(authenticated_client, requests_mock):
    """Test successful order cancellation."""
    url = authenticated_client.configuration.get_url_details("cancel_order")

    requests_mock.post(
        url,
        json={"stat": "Ok", "message": "Order cancelled"},
        status_code=200,
    )

    result = authenticated_client.cancel_order(order_id="240101000000001")

    assert result["stat"] == "Ok"


def test_cancel_order_without_2fa():
    """Test cancel_order without 2FA."""
    client = NeoAPI(environment="prod", consumer_key="test_key")

    result = client.cancel_order(order_id="240101000000001")

    assert "Error Message" in result
    assert "2fa" in result["Error Message"]


def test_cancel_order_with_amo(authenticated_client, requests_mock):
    """Test cancel_order with AMO flag."""
    url = authenticated_client.configuration.get_url_details("cancel_order")

    requests_mock.post(
        url,
        json={"stat": "Ok", "message": "Order cancelled"},
        status_code=200,
    )

    result = authenticated_client.cancel_order(order_id="240101000000001", amo="YES")

    assert result["stat"] == "Ok"


def test_cancel_cover_order_success(authenticated_client, requests_mock):
    """Test successful cover order cancellation."""
    url = authenticated_client.configuration.get_url_details("cancel_cover_order")

    requests_mock.post(
        url,
        json={"stat": "Ok", "message": "Cover order cancelled"},
        status_code=200,
    )

    result = authenticated_client.cancel_cover_order(order_id="240101000000002")

    assert result["stat"] == "Ok"


def test_cancel_cover_order_without_2fa():
    """Test cancel_cover_order without 2FA."""
    client = NeoAPI(environment="prod", consumer_key="test_key")

    result = client.cancel_cover_order(order_id="240101000000002")

    assert "Error Message" in result
    assert "2fa" in result["Error Message"]


def test_cancel_bracket_order_success(authenticated_client, requests_mock):
    """Test successful bracket order cancellation."""
    url = authenticated_client.configuration.get_url_details("cancel_bracket_order")

    requests_mock.post(
        url,
        json={"stat": "Ok", "message": "Bracket order cancelled"},
        status_code=200,
    )

    result = authenticated_client.cancel_bracket_order(order_id="240101000000003")

    assert result["stat"] == "Ok"


def test_cancel_bracket_order_without_2fa():
    """Test cancel_bracket_order without 2FA."""
    client = NeoAPI(environment="prod", consumer_key="test_key")

    result = client.cancel_bracket_order(order_id="240101000000003")

    assert "Error Message" in result
    assert "2fa" in result["Error Message"]


def test_order_report_without_2fa():
    """Test order_report without 2FA."""
    client = NeoAPI(environment="prod", consumer_key="test_key")

    result = client.order_report()

    assert "Error Message" in result
    assert "2fa" in result["Error Message"]


def test_order_history_without_2fa():
    """Test order_history without 2FA."""
    client = NeoAPI(environment="prod", consumer_key="test_key")

    result = client.order_history(order_id="240101000000001")

    assert "Error Message" in result
    assert "2fa" in result["Error Message"]


def test_limits_without_2fa():
    """Test limits without 2FA."""
    client = NeoAPI(environment="prod", consumer_key="test_key")

    result = client.limits()

    assert "Error Message" in result
    assert "2fa" in result["Error Message"]


def test_scrip_master_success(authenticated_client, requests_mock):
    """Test scrip master retrieval."""
    url = authenticated_client.configuration.get_url_details("scrip_master")

    requests_mock.post(
        url,
        json={"stat": "Ok", "message": "Scrip master downloaded"},
        status_code=200,
    )

    result = authenticated_client.scrip_master()

    assert result is not None


def test_scrip_master_without_2fa():
    """Test scrip_master without 2FA."""
    client = NeoAPI(environment="prod", consumer_key="test_key")

    result = client.scrip_master()

    assert "Error Message" in result
    assert "2fa" in result["Error Message"]
