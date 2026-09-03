from json import JSONDecodeError
from unittest.mock import Mock

import pytest

from neo_api_client import NeoAPI
from neo_api_client.services.historical_data import HistoricalDataAPI


def test_get_historical_data_success(requests_mock, api_client):
    url = "https://test-api.kotak.com/market-data/1.0/historical/details"

    requests_mock.get(
        url,
        json={
            "status": "success",
            "interval": "10min",
            "data": {
                "candles": [
                    ["2026-08-20T09:15:00+0530", 100.0, 105.0, 99.0, 103.0, 5000, 12000],
                ]
            },
        },
    )

    response = HistoricalDataAPI(api_client).get_historical_data(
        neosymbol="nse_cm|1333",
        interval="10min",
        from_date="2026-08-20",
        to_date="2026-09-01",
    )

    assert response["status"] == "success"
    assert len(response["data"]["candles"]) == 1


def test_get_historical_data_with_daily_interval(requests_mock, api_client):
    """ "D" (daily) is a supported interval alongside the intraday ones."""
    url = "https://test-api.kotak.com/market-data/1.0/historical/details"

    requests_mock.get(url, json={"status": "success", "interval": "D", "data": {"candles": []}})

    response = HistoricalDataAPI(api_client).get_historical_data(
        neosymbol="nse_cm|1333", interval="D", from_date="2026-01-01", to_date="2026-06-30"
    )

    assert response["status"] == "success"


def test_get_historical_data_json_decode_error(api_client, monkeypatch):
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

    response = HistoricalDataAPI(api_client).get_historical_data(
        neosymbol="nse_cm|1333", interval="10min", from_date="2026-08-20", to_date="2026-09-01"
    )

    assert response["Error"] == "Unexpected response format"
    assert response["StatusCode"] == 500


def test_neo_api_historical_data_requires_totp_validate():
    client = NeoAPI(environment="prod", consumer_key="test_key")

    with pytest.raises(ValueError, match="totp_validate"):
        client.historical_data(
            neosymbol="nse_cm|1333",
            interval="10min",
            from_date="2026-08-20",
            to_date="2026-09-01",
        )
