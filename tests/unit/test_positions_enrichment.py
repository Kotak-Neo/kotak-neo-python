"""Unit tests for the Positions P&L calculation logic -- _enrich_positions_with_pnl(),
_fetch_ltp_for_positions(), and _get_cached_holdings_by_identifier() on NeoAPI.

NOTE: positions() itself does not call any of this. Per product, the backend's
`ltp` field is occasionally `0`, which fed directly into this calculation and
produced incorrect P&L values, so it's intentionally not wired into positions()'s
response (see positions()'s docstring). These tests exercise the calculation
logic directly -- it's kept available for when the upstream LTP reliability
issue is resolved, but not surfaced in the meantime. See
docs/functions/portfolio/positions.md and neo_api_client/utils/positions_pnl.py.
"""

from datetime import timedelta

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


# ---- positions(): raw passthrough, no P&L fields surfaced -------------------


def test_positions_does_not_surface_pnl_fields(requests_mock):
    """positions() must return the raw broker response untouched -- the
    calculation logic is implemented (see the rest of this file) but
    intentionally not wired in, since the backend's ltp is occasionally 0."""
    client = _authenticated_client()
    requests_mock.get(POSITIONS_URL, json={"data": [_equity_cf_position(ltp="120.00")]})

    result = client.positions()

    position = result["data"][0]
    for field in ("netQty", "averagePrice", "positionPnl", "mtmPnl", "pnlCalculationError"):
        assert field not in position
    assert position["tok"] == "61304"  # raw fields pass through untouched
    assert position["ltp"] == "120.00"


def test_positions_without_2fa_returns_existing_error_unchanged():
    """positions() without 2FA must still return the pre-existing error."""
    client = NeoAPI(environment="prod", consumer_key="test_key")

    result = client.positions()

    assert result == {"Error Message": "Complete the 2fa process before accessing this application"}


# ---- holdings(): always live, caches as a side effect -----------------------


def test_holdings_called_twice_in_a_row_always_hits_network_each_time(requests_mock):
    """A direct holdings() call is a live read every time -- it never serves
    from the cache it populates."""
    client = _authenticated_client()
    holdings_route = requests_mock.get(HOLDINGS_URL, json={"data": []})

    client.holdings()
    client.holdings()

    assert holdings_route.call_count == 2


# ---- _get_cached_holdings_by_identifier(): same-day cache-then-fetch -------


def test_get_cached_holdings_by_identifier_fetches_once_then_reuses_in_memory(requests_mock):
    client = _authenticated_client()
    holdings_route = requests_mock.get(
        HOLDINGS_URL, json={"data": [{"exchangeIdentifier": "61304", "averagePrice": 100.0}]}
    )

    first = client._get_cached_holdings_by_identifier()
    second = client._get_cached_holdings_by_identifier()

    assert holdings_route.call_count == 1
    assert first == second == {"61304": {"exchangeIdentifier": "61304", "averagePrice": 100.0}}


def test_get_cached_holdings_by_identifier_reuses_disk_cache_across_clients(requests_mock):
    """The on-disk cache -- not just the in-memory one -- lets a second,
    unrelated NeoAPI instance (e.g. a separate process run the same day)
    reuse holdings() without hitting the network again."""
    holdings_route = requests_mock.get(
        HOLDINGS_URL, json={"data": [{"exchangeIdentifier": "61304", "averagePrice": 100.0}]}
    )
    first_client = _authenticated_client()
    first_client._get_cached_holdings_by_identifier()
    assert holdings_route.call_count == 1

    second_client = _authenticated_client()
    result = second_client._get_cached_holdings_by_identifier()

    assert holdings_route.call_count == 1  # reused the on-disk cache, not refetched
    assert result["61304"]["averagePrice"] == 100.0


def test_get_cached_holdings_by_identifier_refetches_on_a_new_day(requests_mock, monkeypatch):
    """Cross a simulated day boundary -- holdings() must be fetched again."""
    client = _authenticated_client()
    holdings_route = requests_mock.get(
        HOLDINGS_URL, json={"data": [{"exchangeIdentifier": "61304", "averagePrice": 100.0}]}
    )

    client._get_cached_holdings_by_identifier()
    assert holdings_route.call_count == 1

    # Simulate the next calendar day by rewinding the in-memory cache date,
    # and treating the on-disk cache as if it weren't there yet either --
    # it's still written under *today's* real date, which the rewind above
    # doesn't affect.
    client._holdings_cache_date -= timedelta(days=1)
    monkeypatch.setattr(holdings_cache, "read_holdings", lambda ucc: None)

    client._get_cached_holdings_by_identifier()
    assert holdings_route.call_count == 2


def test_get_cached_holdings_by_identifier_failure_not_cached_as_permanent(requests_mock):
    """A transient holdings() failure must not poison the cache for the rest
    of the day -- the next call should retry, and once it succeeds, get the
    real data, not a permanently-cached error."""
    client = _authenticated_client()
    holdings_route = requests_mock.get(HOLDINGS_URL, status_code=500, text="boom")

    first = client._get_cached_holdings_by_identifier()
    assert first == {}
    assert client._holdings_cache_date is None  # failure must not be cached
    assert holdings_route.call_count == 1

    # Re-registering the same route updates what it returns on the next match.
    requests_mock.get(
        HOLDINGS_URL, json={"data": [{"exchangeIdentifier": "61304", "averagePrice": 100.0}]}
    )

    second = client._get_cached_holdings_by_identifier()
    assert second["61304"]["averagePrice"] == 100.0
    assert client._holdings_cache_date is not None  # now cached, since it succeeded
    assert holdings_route.call_count == 2


# ---- _enrich_positions_with_pnl: the calculation itself ---------------------


def test_enrich_positions_with_pnl_equity_carry_forward_with_holdings_and_ltp():
    client = _authenticated_client()
    position_list = {"data": [_equity_cf_position(ltp="120.00")]}
    holdings_by_identifier = {"61304": {"exchangeIdentifier": "61304", "averagePrice": 100.0}}

    client._enrich_positions_with_pnl(position_list, holdings_by_identifier)

    position = position_list["data"][0]
    assert position["averagePrice"] == 100.0
    assert position["positionPnl"] == 200.0
    assert position["pnlCalculationError"] is None
    # Original raw fields are untouched, not replaced.
    assert position["tok"] == "61304"
    assert position["upldPrc"] == "0.00"


def test_enrich_positions_with_pnl_fo_carry_forward_uses_cf_amounts_not_holdings():
    """F&O carry-forward has no Holdings entry -- its cost comes from
    cfBuyAmt/cfSellAmt instead, so positionPnl and mtmPnl end up equal."""
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
        "ltp": "950.00",
    }
    position_list = {"data": [fo_position]}

    client._enrich_positions_with_pnl(position_list, {})  # no Holdings entry needed for F&O

    position = position_list["data"][0]
    assert position["averagePrice"] == 1000.0
    assert position["positionPnl"] == position["mtmPnl"]


def test_enrich_positions_with_pnl_no_matching_holdings_reports_error():
    """No matching Holdings entry for an equity carry-forward position must
    degrade gracefully -- never a silently-wrong average=LTP."""
    client = _authenticated_client()
    position_list = {"data": [_equity_cf_position(ltp="120.00")]}

    client._enrich_positions_with_pnl(position_list, {})  # no holdings entry

    position = position_list["data"][0]
    assert position["averagePrice"] is None
    assert "No matching Holdings entry" in position["pnlCalculationError"]


def test_enrich_positions_with_pnl_quotes_failure_reports_ltp_unavailable():
    client = _authenticated_client()

    def raising_quotes(instrument_tokens=None, quote_type=None):
        raise RuntimeError("boom")

    client.quotes = raising_quotes
    position_list = {"data": [_equity_cf_position()]}  # no own ltp -> needs quotes()
    holdings_by_identifier = {"61304": {"averagePrice": 100.0}}

    client._enrich_positions_with_pnl(position_list, holdings_by_identifier)

    position = position_list["data"][0]
    assert position["averagePrice"] == 100.0
    assert position["positionPnl"] is None
    assert "LTP unavailable" in position["pnlCalculationError"]


def test_enrich_positions_with_pnl_uses_own_ltp_field_skips_quotes_entirely(requests_mock):
    """portfolio/v2/positions returns its own `ltp` per position -- when
    every position already carries it, quotes() must not be called at all."""
    client = _authenticated_client()
    position_list = {"data": [_equity_cf_position(ltp="120.00")]}
    holdings_by_identifier = {"61304": {"averagePrice": 100.0}}
    # Deliberately no quotes() route registered -- if the code tried to call
    # it, respx would raise (no matching mock), failing this test.

    client._enrich_positions_with_pnl(position_list, holdings_by_identifier)

    position = position_list["data"][0]
    assert position["averagePrice"] == 100.0
    assert position["positionPnl"] == 200.0
    assert position["pnlCalculationError"] is None


def test_enrich_positions_with_pnl_non_dict_position_list_is_noop():
    """A malformed (non-dict) position_list must be a no-op, not a crash --
    defensive against a future backend response shape change."""
    client = _authenticated_client()
    assert client._enrich_positions_with_pnl(["not", "a", "dict"], {}) is None


def test_enrich_positions_with_pnl_empty_or_non_list_data_is_noop():
    """A `data` key that's missing, empty, or not a list (e.g. a malformed
    backend response) must be a no-op, not a crash."""
    client = _authenticated_client()
    assert client._enrich_positions_with_pnl({"data": []}, {}) is None
    assert client._enrich_positions_with_pnl({"data": "not-a-list"}, {}) is None
    assert client._enrich_positions_with_pnl({}, {}) is None


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


# ---- _fetch_ltp_for_positions: LTP resolution (own field + quotes fallback) -


def test_fetch_ltp_batched_across_multiple_positions_in_one_quotes_call():
    """Two distinct instruments must go into ONE quotes() call, not two."""
    client = _authenticated_client()
    captured = {}

    def fake_quotes(instrument_tokens=None, quote_type=None):
        captured["tokens"] = instrument_tokens
        return {
            "data": [
                {"exchange": "nse_cm", "exchange_token": "61304", "ltp": "120.00"},
                {"exchange": "nse_cm", "exchange_token": "61305", "ltp": "210.00"},
            ]
        }

    client.quotes = fake_quotes
    positions_data = [_equity_cf_position(tok="61304"), _equity_cf_position(tok="61305")]

    result = client._fetch_ltp_for_positions(positions_data)

    assert len(captured["tokens"]) == 2  # one call, both tokens batched
    assert result["nse_cm|61304"] == 120.0
    assert result["nse_cm|61305"] == 210.0


def test_fetch_ltp_mixed_only_positions_missing_it_go_to_quotes():
    """One position carries its own ltp, the other doesn't (e.g. an older
    backend response) -- only the latter should end up in the quotes() batch."""
    client = _authenticated_client()
    captured = {}

    def fake_quotes(instrument_tokens=None, quote_type=None):
        captured["tokens"] = instrument_tokens
        return {"data": [{"exchange": "nse_cm", "exchange_token": "61305", "ltp": "210.00"}]}

    client.quotes = fake_quotes
    positions_data = [
        _equity_cf_position(tok="61304", ltp="120.00"),  # has its own ltp
        _equity_cf_position(tok="61305"),  # missing -- must fall back to quotes()
    ]

    result = client._fetch_ltp_for_positions(positions_data)

    assert len(captured["tokens"]) == 1  # only the second position needed a lookup
    assert captured["tokens"][0]["instrument_token"] == "61305"
    assert result["nse_cm|61304"] == 120.0
    assert result["nse_cm|61305"] == 210.0


def test_fetch_ltp_unparseable_on_position_falls_back_to_quotes():
    """A garbage `ltp` value on the position (e.g. a future backend quirk)
    must not be trusted silently -- fall back to quotes() instead."""
    client = _authenticated_client()
    client.quotes = lambda instrument_tokens=None, quote_type=None: {
        "data": [{"exchange": "nse_cm", "exchange_token": "61304", "ltp": "120.00"}]
    }

    result = client._fetch_ltp_for_positions([_equity_cf_position(tok="61304", ltp="not-a-number")])

    assert result["nse_cm|61304"] == 120.0


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


def test_fetch_ltp_accepts_quotes_response_as_a_bare_list():
    """quotes() can return a bare list (not wrapped in {"data": [...]}) --
    this must be used directly, not treated as "no quotes"."""
    client = _authenticated_client()
    client.quotes = lambda instrument_tokens=None, quote_type=None: [
        {"exchange": "nse_cm", "exchange_token": "61304", "ltp": "120.00"}
    ]

    result = client._fetch_ltp_for_positions([_equity_cf_position(tok="61304")])

    assert result == {"nse_cm|61304": 120.0}


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
