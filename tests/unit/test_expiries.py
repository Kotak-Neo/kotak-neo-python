from json import JSONDecodeError
from unittest.mock import Mock

from neo_api_client import NeoAPI
from neo_api_client.services.expiries import ExpiriesAPI


def test_get_expiries_success(requests_mock, api_client):
    url = "https://test-api.kotak.com/market-data/1.0/watchlist/expiries"

    requests_mock.get(
        url,
        json={
            "exchange": "nse_fo",
            "underlying": "RELIANCE",
            "expiries": ["2026-06-25", "2026-06-30", "2026-07-31"],
        },
    )

    response = ExpiriesAPI(api_client).get_expiries(exchange="nse_fo", underlying="RELIANCE")

    assert response["exchange"] == "nse_fo"
    assert response["expiries"] == ["2026-06-25", "2026-06-30", "2026-07-31"]


def test_get_expiries_with_instrument_type(requests_mock, api_client):
    url = "https://test-api.kotak.com/market-data/1.0/watchlist/expiries"

    requests_mock.get(url, json={"exchange": "mcx_fo", "underlying": "CRUDEOIL", "expiries": []})

    response = ExpiriesAPI(api_client).get_expiries(
        exchange="mcx_fo", underlying="CRUDEOIL", instrument_type="fut"
    )

    assert response["exchange"] == "mcx_fo"


def test_get_expiries_json_decode_error(api_client, monkeypatch):
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

    response = ExpiriesAPI(api_client).get_expiries(exchange="nse_fo", underlying="RELIANCE")

    assert response["Error"] == "Unexpected response format"
    assert response["StatusCode"] == 500


def test_neo_api_expiries_without_totp_validate(requests_mock):
    """Like quotes()/scrip_master(), expiries() doesn't need totp_validate()
    -- it routes through get_url_details(), which falls back to the shared
    gateway domain when base_url hasn't been populated yet."""
    client = NeoAPI(environment="prod", consumer_key="test_key")
    url = "https://mis.kotaksecurities.com/market-data/1.0/watchlist/expiries"

    requests_mock.get(
        url,
        json={"exchange": "nse_fo", "underlying": "RELIANCE", "expiries": ["2026-06-25"]},
    )

    result = client.expiries(exchange="nse_fo", underlying="RELIANCE")

    assert result["expiries"] == ["2026-06-25"]
