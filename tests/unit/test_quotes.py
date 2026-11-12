from json import JSONDecodeError
from unittest.mock import Mock

from neo_api_client.services import quotes as _quotes_mod
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


def test_get_quotes_429_surfaces_retry_after(requests_mock, api_client):
    """A 429 that carries a Retry-After header surfaces it to the caller,
    giving them a concrete value to back off on."""
    instrument_tokens = [{"exchange_segment": "nse_cm", "instrument_token": "12345"}]
    url = api_client.configuration.get_url_details("quotes_neo_symbol").format(
        neo_symbols="nse_cm|12345",
        quote_type="all",
    )

    requests_mock.get(
        url,
        json={"stat": "Not_Ok", "emsg": "Rate limit exceeded"},
        status_code=429,
        headers={"Retry-After": "60"},
    )

    response = QuotesAPI(api_client).get_quotes(instrument_tokens=instrument_tokens)

    assert response["stat"] == "Not_Ok"
    assert response["rateLimit"] == {"Retry-After": "60"}


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


def test_get_quotes_logs_per_quote_summary_at_info_and_raw_body_at_debug(
    requests_mock, api_client, monkeypatch
):
    """The real backend response is a top-level list (see
    docs/functions/market_data/quotes.md), not a {"data": [...]} wrapper.
    A per-quote summary (including lstup_time) must be logged at INFO --
    small enough to never hit the REST client's own truncation -- and the
    full raw body at DEBUG, so an unexpected lstup_time value (e.g. a
    malformed backend timestamp) is always visible in the log file."""
    instrument_tokens = [{"exchange_segment": "nse_fo", "instrument_token": "127150"}]
    url = api_client.configuration.get_url_details("quotes_neo_symbol").format(
        neo_symbols="nse_fo|127150",
        quote_type="all",
    )
    quote = {
        "exchange_token": "127150",
        "display_symbol": "SBIN26NOV960CE",
        "exchange": "nse_fo",
        "lstup_time": "Mon Jan 01 1900 05:21:10 GMT+0521 (India Standard Time)",
        "ltp": "27.65",
    }
    requests_mock.get(url, json=[quote])

    info_calls = []
    debug_calls = []
    monkeypatch.setattr(
        _quotes_mod.logger, "info", lambda event, **kw: info_calls.append((event, kw))
    )
    monkeypatch.setattr(
        _quotes_mod.logger, "debug", lambda event, **kw: debug_calls.append((event, kw))
    )

    response = QuotesAPI(api_client).get_quotes(instrument_tokens=instrument_tokens)

    assert response == [quote]

    assert len(info_calls) == 1
    event, kw = info_calls[0]
    assert event == "quotes_received"
    assert kw["count"] == 1
    assert kw["quotes"][0]["lstup_time"] == quote["lstup_time"]
    assert kw["quotes"][0]["exchange_token"] == "127150"

    assert len(debug_calls) == 1
    event, kw = debug_calls[0]
    assert event == "quotes_response_raw"
    assert kw["response"] == [quote]


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
