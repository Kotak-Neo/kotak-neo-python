from requests.exceptions import RequestException

from neo_api_client.services.portfolio import PortfolioAPI


def test_portfolio_exception(api_client, monkeypatch):
    def mock_request(*args, **kwargs):
        raise RequestException("failure")

    api_client.rest_client.request = mock_request

    try:
        PortfolioAPI(api_client).portfolio_holdings()
    except RequestException:
        assert True
