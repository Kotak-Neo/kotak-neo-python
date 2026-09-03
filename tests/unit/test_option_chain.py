from json import JSONDecodeError
from unittest.mock import Mock

import pytest

from neo_api_client import NeoAPI
from neo_api_client.services.option_chain import OptionChainAPI


def test_get_option_chain_success(requests_mock, api_client):
    url = "https://test-api.kotak.com/market-data/1.0/watchlist/option-chain"

    requests_mock.get(
        url,
        json={
            "data": {
                "common_data": {"unlSymbol": "RELIANCE"},
                "call": [{"instrument": {"symbol": "RELIANCE26JUN1500CE"}}],
                "put": [{"instrument": {"symbol": "RELIANCE26JUN1500PE"}}],
            }
        },
    )

    response = OptionChainAPI(api_client).get_option_chain(exchange="nse_fo", underlying="RELIANCE")

    assert len(response["data"]["call"]) == 1
    assert len(response["data"]["put"]) == 1


def test_get_option_chain_with_all_params(requests_mock, api_client):
    url = "https://test-api.kotak.com/market-data/1.0/watchlist/option-chain"

    requests_mock.get(url, json={"data": {"call": [], "put": []}})

    response = OptionChainAPI(api_client).get_option_chain(
        exchange="nse_fo",
        underlying="RELIANCE",
        expiry="2026-06-23",
        instrument_type="option",
        count=40,
    )

    assert response["data"]["call"] == []


def test_get_option_chain_futures(requests_mock, api_client):
    """instrumentType=fut returns a fut[] array instead of call/put."""
    url = "https://test-api.kotak.com/market-data/1.0/watchlist/option-chain"

    requests_mock.get(url, json={"data": {"call": [], "put": [], "fut": [{"inst": {}}]}})

    response = OptionChainAPI(api_client).get_option_chain(
        exchange="nse_fo", underlying="NIFTY", instrument_type="fut"
    )

    assert len(response["data"]["fut"]) == 1


def test_get_option_chain_json_decode_error(api_client, monkeypatch):
    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_response.headers = {"Content-Type": "text/plain"}
    mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "doc", 0)

    monkeypatch.setattr(
        api_client.rest_client,
        "request",
        lambda *args, **kwargs: mock_response,
    )

    response = OptionChainAPI(api_client).get_option_chain(exchange="nse_fo", underlying="RELIANCE")

    assert response["Error"] == "Unexpected response format"
    assert response["StatusCode"] == 500


def test_neo_api_option_chain_requires_totp_validate():
    client = NeoAPI(environment="prod", consumer_key="test_key")

    with pytest.raises(ValueError, match="totp_validate"):
        client.option_chain(exchange="nse_fo", underlying="RELIANCE")
