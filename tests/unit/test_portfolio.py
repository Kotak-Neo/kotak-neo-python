import httpx
import pytest

from neo_api_client.services.portfolio import PortfolioAPI


def test_portfolio_exception(api_client, monkeypatch):
    def mock_request(*args, **kwargs):
        raise httpx.HTTPError("failure")

    api_client.rest_client.request = mock_request

    # portfolio_holdings() doesn't swallow an unexpected transport error.
    with pytest.raises(httpx.HTTPError):
        PortfolioAPI(api_client).portfolio_holdings()


def test_portfolio_holdings_non_json_error_response(api_client, requests_mock):
    """A 5xx with an empty/non-JSON body returns a structured error dict
    instead of letting a raw JSONDecodeError propagate."""
    url = api_client.configuration.get_url_details("holdings")
    requests_mock.get(url, text="", status_code=503)

    result = PortfolioAPI(api_client).portfolio_holdings()

    assert result["StatusCode"] == 503
    assert result["RequestURL"] == url
    assert "Error" in result
