"""Unit tests for NeoAPI.positions()'s P&L enrichment: holdings() caching,
LTP batching via quotes(), and graceful degradation. See
docs/functions/portfolio/positions.md and neo_api_client/utils/positions_pnl.py."""

from neo_api_client import NeoAPI
from neo_api_client.utils import holdings_cache

POSITIONS_URL = "https://mis.kotaksecurities.com/portfolio/v2/positions"
HOLDINGS_URL = "https://mis.kotaksecurities.com/portfolio/v1/holdings"
QUOTES_URL_TEMPLATE = "https://mis.kotaksecurities.com/script-details/1.0/quotes/neosymbol/{}/ltp"


def _authenticated_client():
    client = NeoAPI(environment="prod", consumer_key="test_key")
    client.configuration.edit_token = "edit_token_123"
    client.configuration.edit_sid = "edit_sid_123"
    client.configuration.base_url = "https://mis.kotaksecurities.com"
    client.configuration.ucc = "TESTUCC1"
    return client


def _equity_cf_position(tok="61304", cf_buy_qty="10", ltp=None):
    position = {
        "tok": tok,
        "exSeg": "nse_cm",
        "cfBuyQty": cf_buy_qty,
        "cfSellQty": "0",
        "flBuyQty": "0",
        "flSellQty": "0",
        "buyAmt": "0.00",
        "sellAmt": "0.00",
        "cfBuyAmt": "0.00",
        "cfSellAmt": "0.00",
        "multiplier": "1",
        "genNum": "1",
        "genDen": "1",
        "prcNum": "1",
        "prcDen": "1",
        "precision": "2",
        "upldPrc": "0.00",
    }
    if ltp is not None:
        position["ltp"] = ltp
    return position


def test_positions_enriches_equity_carry_forward_with_holdings_and_ltp(requests_mock):
    client = _authenticated_client()
    requests_mock.get(POSITIONS_URL, json={"data": [_equity_cf_position()]})
    requests_mock.get(
        HOLDINGS_URL, json={"data": [{"exchangeIdentifier": "61304", "averagePrice": 100.0}]}
    )
    requests_mock.get(
        QUOTES_URL_TEMPLATE.format("nse_cm|61304"),
        json=[{"exchange": "nse_cm", "exchange_token": "61304", "ltp": "120.00"}],
    )

    result = client.positions()

    position = result["data"][0]
    assert position["averagePrice"] == 100.0
    assert position["positionPnl"] == 200.0
    assert position["pnlCalculationError"] is None
    # Original raw fields are untouched, not replaced.
    assert position["tok"] == "61304"
    assert position["upldPrc"] == "0.00"


def test_explicit_holdings_call_primes_the_cache_positions_reuses(requests_mock):
    """If the caller already fetched holdings() themselves, positions()
    should reuse that instead of fetching it again."""
    client = _authenticated_client()
    holdings_route = requests_mock.get(
        HOLDINGS_URL, json={"data": [{"exchangeIdentifier": "61304", "averagePrice": 100.0}]}
    )
    requests_mock.get(POSITIONS_URL, json={"data": [_equity_cf_position(ltp="120.00")]})

    client.holdings()
    assert holdings_route.call_count == 1

    result = client.positions()

    assert holdings_route.call_count == 1  # not called again
    assert result["data"][0]["averagePrice"] == 100.0


def test_positions_then_explicit_holdings_call_still_goes_live(requests_mock):
    """The exact smoke_test.py scenario: POSITIONS runs (triggering
    holdings() internally), then a separate, explicit HOLDINGS call runs
    right after -- an explicit holdings() call is a live read, so it must
    hit the network again even though positions() just cached a response."""
    client = _authenticated_client()
    holdings_payload = {
        "data": [{"exchangeIdentifier": "61304", "averagePrice": 100.0, "mktValue": 12345.0}]
    }
    holdings_route = requests_mock.get(HOLDINGS_URL, json=holdings_payload)
    requests_mock.get(POSITIONS_URL, json={"data": [_equity_cf_position(ltp="120.00")]})

    client.positions()
    assert holdings_route.call_count == 1

    result = client.holdings()

    assert holdings_route.call_count == 2  # explicit call always goes live
    assert result == holdings_payload


def test_holdings_called_twice_in_a_row_always_hits_network_each_time(requests_mock):
    """A direct holdings() call is a live read every time -- it never serves
    from the cache it populates, unlike positions()'s internal use of it."""
    client = _authenticated_client()
    holdings_route = requests_mock.get(HOLDINGS_URL, json={"data": []})

    client.holdings()
    client.holdings()

    assert holdings_route.call_count == 2


def test_holdings_fetched_once_per_day_across_multiple_positions_calls(requests_mock, monkeypatch):
    """The whole point of caching: two positions() calls the same day must
    only trigger one holdings() request."""
    client = _authenticated_client()
    requests_mock.get(POSITIONS_URL, json={"data": [_equity_cf_position()]})
    holdings_route = requests_mock.get(
        HOLDINGS_URL, json={"data": [{"exchangeIdentifier": "61304", "averagePrice": 100.0}]}
    )
    requests_mock.get(
        QUOTES_URL_TEMPLATE.format("nse_cm|61304"),
        json=[{"exchange": "nse_cm", "exchange_token": "61304", "ltp": "120.00"}],
    )

    client.positions()
    client.positions()
    client.positions()

    assert holdings_route.call_count == 1


def test_holdings_refetched_on_a_new_day(requests_mock, monkeypatch):
    """Cross a simulated day boundary -- holdings() must be fetched again."""
    client = _authenticated_client()
    requests_mock.get(POSITIONS_URL, json={"data": [_equity_cf_position()]})
    holdings_route = requests_mock.get(
        HOLDINGS_URL, json={"data": [{"exchangeIdentifier": "61304", "averagePrice": 100.0}]}
    )
    requests_mock.get(
        QUOTES_URL_TEMPLATE.format("nse_cm|61304"),
        json=[{"exchange": "nse_cm", "exchange_token": "61304", "ltp": "120.00"}],
    )

    client.positions()
    assert holdings_route.call_count == 1

    # Simulate the next calendar day by rewinding the in-memory cache date,
    # and treating the on-disk cache as if it weren't there yet either --
    # it's still written under *today's* real date, which the rewind above
    # doesn't affect.
    from datetime import timedelta

    client._holdings_cache_date -= timedelta(days=1)
    monkeypatch.setattr(holdings_cache, "read_holdings", lambda ucc: None)

    client.positions()
    assert holdings_route.call_count == 2


def test_holdings_cache_survives_a_fresh_client_same_day(requests_mock):
    """The on-disk cache -- not just the in-memory one -- must let a second,
    unrelated NeoAPI instance (e.g. a separate run of smoke_test.py the same
    day) reuse holdings() without hitting the network again."""
    holdings_route = requests_mock.get(
        HOLDINGS_URL, json={"data": [{"exchangeIdentifier": "61304", "averagePrice": 100.0}]}
    )
    requests_mock.get(POSITIONS_URL, json={"data": [_equity_cf_position(ltp="120.00")]})

    first_client = _authenticated_client()
    first_client.positions()
    assert holdings_route.call_count == 1

    # A brand-new client -- no in-memory state at all -- standing in for a
    # fresh process, same account (UCC), same day.
    second_client = _authenticated_client()
    result = second_client.positions()

    assert holdings_route.call_count == 1  # reused the on-disk cache, not refetched
    assert result["data"][0]["averagePrice"] == 100.0


def test_fo_only_positions_still_call_holdings_but_dont_need_it(requests_mock):
    """Per product: holdings() is called unconditionally (before positions()
    itself), so every account pays for it once a day regardless of segment
    mix -- but F&O carry-forward still correctly sources its cost from
    cfBuyAmt/cfSellAmt, not from whatever (or nothing) holdings() returned."""
    client = _authenticated_client()
    fo_position = {
        "tok": "70001",
        "exSeg": "nse_fo",
        "cfBuyQty": "0",
        "cfSellQty": "5",
        "flBuyQty": "0",
        "flSellQty": "0",
        "buyAmt": "0.00",
        "sellAmt": "0.00",
        "cfBuyAmt": "0.00",
        "cfSellAmt": "5000.00",
        "multiplier": "1",
        "genNum": "1",
        "genDen": "1",
        "prcNum": "1",
        "prcDen": "1",
        "precision": "2",
    }
    requests_mock.get(POSITIONS_URL, json={"data": [fo_position]})
    holdings_route = requests_mock.get(HOLDINGS_URL, json={"data": []})
    requests_mock.get(
        QUOTES_URL_TEMPLATE.format("nse_fo|70001"),
        json=[{"exchange": "nse_fo", "exchange_token": "70001", "ltp": "950.00"}],
    )

    result = client.positions()

    assert holdings_route.call_count == 1
    position = result["data"][0]
    assert position["averagePrice"] == 1000.0
    assert position["positionPnl"] == position["mtmPnl"]


def test_empty_positions_list_still_fetches_holdings_but_skips_quotes(requests_mock):
    """holdings() is fetched before positions() even returns, so it happens
    regardless of what positions() comes back with; quotes() has nothing to
    fetch LTP for, so it's correctly skipped."""
    client = _authenticated_client()
    requests_mock.get(POSITIONS_URL, json={"data": []})
    holdings_route = requests_mock.get(HOLDINGS_URL, json={"data": []})

    result = client.positions()

    assert holdings_route.call_count == 1
    assert result["data"] == []


def test_holdings_failure_reports_error_without_breaking_positions(requests_mock):
    """If holdings() itself comes back as an error dict (not {"data": [...]}),
    enrichment must degrade gracefully -- not raise, not crash positions()."""
    client = _authenticated_client()
    requests_mock.get(POSITIONS_URL, json={"data": [_equity_cf_position()]})
    requests_mock.get(HOLDINGS_URL, status_code=500, text="Internal Server Error")
    requests_mock.get(
        QUOTES_URL_TEMPLATE.format("nse_cm|61304"),
        json=[{"exchange": "nse_cm", "exchange_token": "61304", "ltp": "120.00"}],
    )

    result = client.positions()

    position = result["data"][0]
    assert position["averagePrice"] is None
    assert "No matching Holdings entry" in position["pnlCalculationError"]


def test_holdings_failure_is_retried_on_next_call_same_day_not_cached_as_permanent(requests_mock):
    """The actual bug this design avoids: a transient holdings() failure on
    the first positions() call of the day must NOT poison the cache for the
    rest of the day -- the next positions() call should retry holdings(),
    and once it succeeds, positions get real P&L, not a permanently-cached
    error."""
    client = _authenticated_client()
    requests_mock.get(POSITIONS_URL, json={"data": [_equity_cf_position()]})
    requests_mock.get(
        QUOTES_URL_TEMPLATE.format("nse_cm|61304"),
        json=[{"exchange": "nse_cm", "exchange_token": "61304", "ltp": "120.00"}],
    )
    holdings_route = requests_mock.get(HOLDINGS_URL, status_code=500, text="boom")

    first = client.positions()
    assert first["data"][0]["averagePrice"] is None
    assert client._holdings_cache_date is None  # failure must not be cached
    assert holdings_route.call_count == 1

    # Second call, same day: holdings() now succeeds (re-registering the same
    # route updates what it returns on the next match).
    requests_mock.get(
        HOLDINGS_URL, json={"data": [{"exchangeIdentifier": "61304", "averagePrice": 100.0}]}
    )

    second = client.positions()

    assert second["data"][0]["averagePrice"] == 100.0
    assert second["data"][0]["positionPnl"] == 200.0
    assert client._holdings_cache_date is not None  # now cached, since it succeeded


def test_quotes_failure_reports_ltp_unavailable_but_keeps_average_price(requests_mock):
    client = _authenticated_client()
    requests_mock.get(POSITIONS_URL, json={"data": [_equity_cf_position()]})
    requests_mock.get(
        HOLDINGS_URL, json={"data": [{"exchangeIdentifier": "61304", "averagePrice": 100.0}]}
    )
    requests_mock.get(QUOTES_URL_TEMPLATE.format("nse_cm|61304"), status_code=500, text="boom")

    result = client.positions()

    position = result["data"][0]
    assert position["averagePrice"] == 100.0
    assert position["positionPnl"] is None
    assert "LTP unavailable" in position["pnlCalculationError"]


def test_ltp_batched_across_multiple_positions_in_one_quotes_call(requests_mock):
    """Two distinct instruments must go into ONE quotes() call, not two."""
    client = _authenticated_client()
    positions_data = [_equity_cf_position(tok="61304"), _equity_cf_position(tok="61305")]
    requests_mock.get(POSITIONS_URL, json={"data": positions_data})
    requests_mock.get(
        HOLDINGS_URL,
        json={
            "data": [
                {"exchangeIdentifier": "61304", "averagePrice": 100.0},
                {"exchangeIdentifier": "61305", "averagePrice": 200.0},
            ]
        },
    )
    quotes_route = requests_mock.get(
        QUOTES_URL_TEMPLATE.format("nse_cm|61304,nse_cm|61305"),
        json=[
            {"exchange": "nse_cm", "exchange_token": "61304", "ltp": "120.00"},
            {"exchange": "nse_cm", "exchange_token": "61305", "ltp": "210.00"},
        ],
    )

    result = client.positions()

    assert quotes_route.call_count == 1
    assert result["data"][0]["averagePrice"] == 100.0
    assert result["data"][1]["averagePrice"] == 200.0


def test_ltp_from_positions_response_used_directly_skips_quotes_entirely(requests_mock):
    """portfolio/v2/positions now returns its own `ltp` per position -- when
    every position already carries it, quotes() must not be called at all."""
    client = _authenticated_client()
    requests_mock.get(POSITIONS_URL, json={"data": [_equity_cf_position(ltp="120.00")]})
    requests_mock.get(
        HOLDINGS_URL, json={"data": [{"exchangeIdentifier": "61304", "averagePrice": 100.0}]}
    )
    # Deliberately no quotes() route registered -- if the code tried to call
    # it, respx would raise (no matching mock), failing this test.

    result = client.positions()

    position = result["data"][0]
    assert position["averagePrice"] == 100.0
    assert position["positionPnl"] == 200.0
    assert position["pnlCalculationError"] is None


def test_ltp_mixed_only_positions_missing_it_go_to_quotes(requests_mock):
    """One position carries its own ltp, the other doesn't (e.g. an older
    backend response) -- only the latter should end up in the quotes() batch."""
    client = _authenticated_client()
    positions_data = [
        _equity_cf_position(tok="61304", ltp="120.00"),  # has its own ltp
        _equity_cf_position(tok="61305"),  # missing -- must fall back to quotes()
    ]
    requests_mock.get(POSITIONS_URL, json={"data": positions_data})
    requests_mock.get(
        HOLDINGS_URL,
        json={
            "data": [
                {"exchangeIdentifier": "61304", "averagePrice": 100.0},
                {"exchangeIdentifier": "61305", "averagePrice": 200.0},
            ]
        },
    )
    quotes_route = requests_mock.get(
        QUOTES_URL_TEMPLATE.format("nse_cm|61305"),
        json=[{"exchange": "nse_cm", "exchange_token": "61305", "ltp": "210.00"}],
    )

    result = client.positions()

    assert quotes_route.call_count == 1  # only for the second position
    assert result["data"][0]["averagePrice"] == 100.0
    assert result["data"][1]["averagePrice"] == 200.0


def test_ltp_unparseable_on_position_falls_back_to_quotes(requests_mock):
    """A garbage `ltp` value on the position (e.g. a future backend quirk)
    must not be trusted silently -- fall back to quotes() instead."""
    client = _authenticated_client()
    requests_mock.get(POSITIONS_URL, json={"data": [_equity_cf_position(ltp="not-a-number")]})
    requests_mock.get(
        HOLDINGS_URL, json={"data": [{"exchangeIdentifier": "61304", "averagePrice": 100.0}]}
    )
    quotes_route = requests_mock.get(
        QUOTES_URL_TEMPLATE.format("nse_cm|61304"),
        json=[{"exchange": "nse_cm", "exchange_token": "61304", "ltp": "120.00"}],
    )

    result = client.positions()

    assert quotes_route.call_count == 1
    assert result["data"][0]["positionPnl"] == 200.0


def test_positions_without_2fa_returns_existing_error_unchanged():
    """Enrichment must not change the pre-existing "complete 2FA" error path."""
    client = NeoAPI(environment="prod", consumer_key="test_key")

    result = client.positions()

    assert result == {"Error Message": "Complete the 2fa process before accessing this application"}


# ---- _enrich_positions_with_pnl / _fetch_ltp_for_positions edge cases ------


def test_enrich_positions_with_pnl_non_dict_position_list_is_noop():
    """A malformed (non-dict) position_list must be a no-op, not a crash --
    defensive against a future backend response shape change."""
    client = _authenticated_client()
    assert client._enrich_positions_with_pnl(["not", "a", "dict"], {}) is None


def test_enrich_positions_with_pnl_and_fetch_ltp_skip_non_dict_entries():
    """A malformed (non-dict) entry inside positions_data must be skipped by
    both _enrich_positions_with_pnl's own loop and _fetch_ltp_for_positions
    (which it calls first), not crash either one."""
    client = _authenticated_client()
    positions_data = ["not-a-dict", {"exSeg": None, "tok": None}]

    client._enrich_positions_with_pnl({"data": positions_data}, {})

    # The non-dict entry is untouched; the dict entry got no exSeg/tok so no
    # quotes() lookup was attempted, but it was still processed (not skipped).
    assert positions_data[0] == "not-a-dict"
    assert "pnlCalculationError" in positions_data[1]


def test_fetch_ltp_dedupes_positions_sharing_the_same_key():
    """Two positions with the same exSeg|tok (e.g. two legs of the same
    instrument) must only generate one quotes() lookup, not one each."""
    client = _authenticated_client()
    captured = {}

    def fake_quotes(instrument_tokens=None, quote_type=None):
        captured["tokens"] = instrument_tokens
        return {"data": [{"exchange": "nse_cm", "exchange_token": "61304", "ltp": "120.00"}]}

    client.quotes = fake_quotes

    positions_data = [
        _equity_cf_position(tok="61304"),
        _equity_cf_position(tok="61304"),
    ]
    result = client._fetch_ltp_for_positions(positions_data)

    assert len(captured["tokens"]) == 1  # deduped, not one per position
    assert result["nse_cm|61304"] == 120.0


def test_fetch_ltp_quotes_call_raising_is_swallowed():
    """A quotes() call that raises outright (not just an error dict) must
    not break LTP resolution for other batches -- best-effort."""
    client = _authenticated_client()

    def raising_quotes(instrument_tokens=None, quote_type=None):
        raise RuntimeError("boom")

    client.quotes = raising_quotes

    result = client._fetch_ltp_for_positions([_equity_cf_position(tok="61304")])

    assert result == {}


def test_fetch_ltp_quotes_response_of_unexpected_type_is_ignored():
    """A quotes() response that's neither a list nor a dict (e.g. None, from
    some unexpected backend shape) must be treated as "no quotes", not crash."""
    client = _authenticated_client()
    client.quotes = lambda instrument_tokens=None, quote_type=None: None

    result = client._fetch_ltp_for_positions([_equity_cf_position(tok="61304")])

    assert result == {}


def test_fetch_ltp_skips_non_dict_quote_entries():
    """A malformed (non-dict) entry in the quotes() response list must be
    skipped, not crash -- other, well-formed entries in the same batch are
    still processed."""
    client = _authenticated_client()
    client.quotes = lambda instrument_tokens=None, quote_type=None: {
        "data": ["not-a-dict", {"exchange": "nse_cm", "exchange_token": "61304", "ltp": "120.00"}]
    }

    result = client._fetch_ltp_for_positions([_equity_cf_position(tok="61304")])

    assert result == {"nse_cm|61304": 120.0}


def test_fetch_ltp_skips_quote_entries_missing_exchange_token_or_ltp():
    """A quote entry missing exchange/exchange_token/ltp must be skipped
    rather than raising on the subsequent lookup."""
    client = _authenticated_client()
    client.quotes = lambda instrument_tokens=None, quote_type=None: {
        "data": [{"exchange": "nse_cm", "exchange_token": "61304", "ltp": None}]
    }

    result = client._fetch_ltp_for_positions([_equity_cf_position(tok="61304")])

    assert result == {}


def test_fetch_ltp_skips_unparseable_ltp_in_quotes_response():
    """An unparseable `ltp` string *in the quotes() response itself* (as
    opposed to on the position, which has its own dedicated test) must be
    skipped, not raise."""
    client = _authenticated_client()
    client.quotes = lambda instrument_tokens=None, quote_type=None: {
        "data": [{"exchange": "nse_cm", "exchange_token": "61304", "ltp": "not-a-number"}]
    }

    result = client._fetch_ltp_for_positions([_equity_cf_position(tok="61304")])

    assert result == {}
