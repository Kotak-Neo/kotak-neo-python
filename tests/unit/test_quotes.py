from json import JSONDecodeError
from unittest.mock import Mock

from neo_api_client.services.quotes import QuotesAPI


def test_get_quotes_success(requests_mock, api_client):
    instrument_tokens = [
        {
            "exchange_segment": "nse_cm",
            "instrument_token": "12345",
        }
    ]

    encoded_symbol = "nse_cm|12345"

    url = api_client.configuration.get_url_details("quotes_neo_symbol").format(
        neo_symbols=encoded_symbol,
        quote_type="all",
    )

    requests_mock.get(
        url,
        json={
            "stat": "Ok",
            "data": [{"ltp": "100.50"}],
        },
    )

    response = QuotesAPI(api_client).get_quotes(
        instrument_tokens=instrument_tokens,
    )

    assert response["stat"] == "Ok"


def test_get_quotes_custom_quote_type(requests_mock, api_client):
    instrument_tokens = [
        {
            "exchange_segment": "nse_cm",
            "instrument_token": "12345",
        }
    ]

    encoded_symbol = "nse_cm|12345"

    url = api_client.configuration.get_url_details("quotes_neo_symbol").format(
        neo_symbols=encoded_symbol,
        quote_type="ltp",
    )

    requests_mock.get(
        url,
        json={
            "stat": "Ok",
        },
    )

    response = QuotesAPI(api_client).get_quotes(
        instrument_tokens=instrument_tokens,
        quote_type="ltp",
    )

    assert response["stat"] == "Ok"


def test_get_quotes_multiple_neosymbols(requests_mock, api_client):
    """Multiple instrument_tokens are joined with a literal '|' and ',' in the
    path segment, matching the REST API's multi-symbol format, e.g.
    .../neosymbol/nse_cm|1333,nse_cm|19084/all."""
    instrument_tokens = [
        {
            "exchange_segment": "nse_cm",
            "instrument_token": "1333",
        },
        {
            "exchange_segment": "nse_cm",
            "instrument_token": "19084",
        },
    ]

    url = api_client.configuration.get_url_details("quotes_neo_symbol").format(
        neo_symbols="nse_cm|1333,nse_cm|19084",
        quote_type="all",
    )

    requests_mock.get(
        url,
        json={
            "stat": "Ok",
            "data": [{"ltp": "100.50"}, {"ltp": "2500.00"}],
        },
    )

    response = QuotesAPI(api_client).get_quotes(
        instrument_tokens=instrument_tokens,
    )

    assert response["stat"] == "Ok"
    assert len(response["data"]) == 2


def test_get_quotes_json_decode_error(api_client, monkeypatch):
    mock_response = Mock()

    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"

    mock_response.headers = {
        "Content-Type": "text/plain",
    }

    mock_response.json.side_effect = JSONDecodeError(
        "Invalid JSON",
        "doc",
        0,
    )

    monkeypatch.setattr(
        api_client.rest_client,
        "request",
        lambda *args, **kwargs: mock_response,
    )

    response = QuotesAPI(api_client).get_quotes(
        instrument_tokens=[
            {
                "exchange_segment": "nse_cm",
                "instrument_token": "12345",
            }
        ]
    )

    assert response["Error"] == "Unexpected response format"
    assert response["StatusCode"] == 500
