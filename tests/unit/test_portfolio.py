import httpx
import pytest

from neo_api_client.services.portfolio import PortfolioAPI


def test_portfolio_exception(api_client, monkeypatch):
    def mock_request(*args, **kwargs):
        raise httpx.HTTPError("failure")

    api_client.rest_client.request = mock_request

    # portfolio_holdings() logs and re-raises the transport error.
    with pytest.raises(httpx.HTTPError):
        PortfolioAPI(api_client).portfolio_holdings()
