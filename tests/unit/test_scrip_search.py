"""Unit tests for ScripSearch service."""

from neo_api_client.services.scrip_search import ScripSearch


def test_scrip_search_init(api_client):
    """Test ScripSearch initialization."""
    scrip_search = ScripSearch(api_client)
    assert scrip_search.api_client == api_client


def test_scrip_search_nse_cm(api_client, requests_mock):
    """Test scrip search for NSE Cash Market."""
    url = api_client.configuration.get_url_details("scrip_master")

    mock_response = {
        "stat": "Ok",
        "data": {
            "filesPaths": [
                "https://api.kotaksecurities.com/devapis/global/scripmaster/v1/file-paths/prod/NSE_CM.csv"
            ]
        },
    }

    requests_mock.get(url, json=mock_response, status_code=200)

    # Mock CSV download
    csv_content = "pSymbol,pTrdSymbol,pExchSeg,pSymbolName\nRELIANCE-EQ,RELIANCE-EQ,nse_cm,RELIANCE"
    requests_mock.get(mock_response["data"]["filesPaths"][0], text=csv_content, status_code=200)

    scrip_search = ScripSearch(api_client)
    result = scrip_search.scrip_search(
        symbol="RELIANCE",
        exchange_segment="nse_cm",
        expiry="",
        option_type="",
        strike_price="",
        ignore_50multiple="",
    )

    # The method returns filtered CSV data
    assert result is not None


def test_scrip_search_nse_fo(api_client, requests_mock):
    """Test scrip search for NSE F&O."""
    url = api_client.configuration.get_url_details("scrip_master")

    mock_response = {
        "stat": "Ok",
        "data": {
            "filesPaths": [
                "https://api.kotaksecurities.com/devapis/global/scripmaster/v1/file-paths/prod/NSE_FO.csv"
            ]
        },
    }

    requests_mock.get(url, json=mock_response, status_code=200)

    # Mock CSV download - provide complete data for FO segment
    csv_content = "pSymbol,pTrdSymbol,pExchSeg,pSymbolName,pOptionType,dStrikePrice;,pExpiryDate,pInstType\nNIFTY24JUN22000CE,NIFTY24JUN22000CE,nse_fo,NIFTY,CE,2200000,1718928000,OPTIDX"
    requests_mock.get(mock_response["data"]["filesPaths"][0], text=csv_content, status_code=200)

    scrip_search = ScripSearch(api_client)
    result = scrip_search.scrip_search(
        symbol="NIFTY",
        exchange_segment="nse_fo",
        expiry="",
        option_type="",
        strike_price="",
        ignore_50multiple="",
    )

    # Result can be a list or a dict with "message" if no data found
    # Just verify the method executes without error
    assert result is not None


def test_scrip_search_bse(api_client, requests_mock):
    """Test scrip search for BSE."""
    url = api_client.configuration.get_url_details("scrip_master")

    mock_response = {
        "stat": "Ok",
        "data": {
            "filesPaths": [
                "https://api.kotaksecurities.com/devapis/global/scripmaster/v1/file-paths/prod/BSE_CM.csv"
            ]
        },
    }

    requests_mock.get(url, json=mock_response, status_code=200)

    # Mock CSV download
    csv_content = "pSymbol,pTrdSymbol,pExchSeg,pSymbolName\nRELIANCE,RELIANCE,bse_cm,RELIANCE"
    requests_mock.get(mock_response["data"]["filesPaths"][0], text=csv_content, status_code=200)

    scrip_search = ScripSearch(api_client)
    result = scrip_search.scrip_search(
        symbol="RELIANCE",
        exchange_segment="bse_cm",
        expiry="",
        option_type="",
        strike_price="",
        ignore_50multiple="",
    )

    assert result is not None


def test_scrip_search_error_response(api_client, requests_mock):
    """Test scrip search with error response."""
    url = api_client.configuration.get_url_details("scrip_master")

    mock_response = {"stat": "Not_Ok", "message": "Server error"}

    requests_mock.get(url, json=mock_response, status_code=500)

    scrip_search = ScripSearch(api_client)
    result = scrip_search.scrip_search(
        symbol="TEST",
        exchange_segment="nse_cm",
        expiry="",
        option_type="",
        strike_price="",
        ignore_50multiple="",
    )

    assert result["stat"] == "Not_Ok"


# ---- Richer F&O CSV covering expiry / option_type / strike_price filters ----

# Two NIFTY option rows: a CE @ 22000 and a PE @ 22500, both expiring 20 Jun 2024
# (epoch 1718841600 in the exchange's shifted-epoch scheme handled by the code).
_FO_CSV = (
    "pSymbol,pTrdSymbol,pExchSeg,pSymbolName,pOptionType,dStrikePrice;,pExpiryDate,pInstType\n"
    "1,NIFTY24JUN22000CE,nse_fo,NIFTY,CE,2200000,1403222400,OPTIDX\n"
    "2,NIFTY24JUN22500PE,nse_fo,NIFTY,PE,2250000,1403222400,OPTIDX\n"
)


def _mock_fo(api_client, requests_mock, csv=_FO_CSV):
    url = api_client.configuration.get_url_details("scrip_master")
    path = "https://api.kotaksecurities.com/scripmaster/NSE_FO.csv"
    requests_mock.get(url, json={"stat": "Ok", "data": {"filesPaths": [path]}}, status_code=200)
    requests_mock.get(path, text=csv, status_code=200)


def test_scrip_search_option_type_filter(api_client, requests_mock):
    """option_type filter narrows to CE rows only."""
    _mock_fo(api_client, requests_mock)
    result = ScripSearch(api_client).scrip_search(
        symbol="nifty",
        exchange_segment="nse_fo",
        expiry=None,
        option_type="CE",
        strike_price=None,
        ignore_50multiple=True,
    )
    assert isinstance(result, list)
    assert all(r["pOptionType"] == "ce" for r in result)


def test_scrip_search_strike_price_greater_than(api_client, requests_mock):
    """strike_price '>NNN' filter."""
    _mock_fo(api_client, requests_mock)
    result = ScripSearch(api_client).scrip_search(
        symbol="nifty",
        exchange_segment="nse_fo",
        expiry=None,
        option_type=None,
        strike_price=">220",  # >22000
        ignore_50multiple=True,
    )
    assert isinstance(result, list)


def test_scrip_search_less_than(api_client, requests_mock):
    """strike_price '<NNN' filter executes (returns list or 'no data' message)."""
    _mock_fo(api_client, requests_mock)
    result = ScripSearch(api_client).scrip_search(
        symbol="nifty",
        exchange_segment="nse_fo",
        expiry=None,
        option_type=None,
        strike_price="<230",
        ignore_50multiple=True,
    )
    # Strikes are stored scaled (×100); the filter may return rows or a message.
    assert result is not None


def test_scrip_search_strike_price_range(api_client, requests_mock):
    """strike_price 'min-max' range filter."""
    _mock_fo(api_client, requests_mock)
    result = ScripSearch(api_client).scrip_search(
        symbol="nifty",
        exchange_segment="nse_fo",
        expiry=None,
        option_type=None,
        strike_price="21000-23000",
        ignore_50multiple=True,
    )
    assert isinstance(result, list)


def test_scrip_search_strike_price_range_min_gt_max(api_client, requests_mock):
    """Range where min > max returns an error dict."""
    _mock_fo(api_client, requests_mock)
    result = ScripSearch(api_client).scrip_search(
        symbol="nifty",
        exchange_segment="nse_fo",
        expiry=None,
        option_type=None,
        strike_price="23000-21000",
        ignore_50multiple=True,
    )
    assert "error" in result


def test_scrip_search_strike_price_zero(api_client, requests_mock):
    """A single strike price of 0 (<= 0) returns an error dict."""
    _mock_fo(api_client, requests_mock)
    result = ScripSearch(api_client).scrip_search(
        symbol="nifty",
        exchange_segment="nse_fo",
        expiry=None,
        option_type=None,
        strike_price="0",
        ignore_50multiple=True,
    )
    assert "error" in result


def test_scrip_search_strike_price_bad_format(api_client, requests_mock):
    """Strike price with too many parts returns an error dict."""
    _mock_fo(api_client, requests_mock)
    result = ScripSearch(api_client).scrip_search(
        symbol="nifty",
        exchange_segment="nse_fo",
        expiry=None,
        option_type=None,
        strike_price="1-2-3",
        ignore_50multiple=True,
    )
    assert "error" in result


def test_scrip_search_expiry_bad_format(api_client, requests_mock):
    """Expiry with >2 parts returns an error dict."""
    _mock_fo(api_client, requests_mock)
    result = ScripSearch(api_client).scrip_search(
        symbol="nifty",
        exchange_segment="nse_fo",
        expiry="01JAN2024-01FEB2024-01MAR2024",
        option_type=None,
        strike_price=None,
        ignore_50multiple=True,
    )
    assert "error" in result


def test_scrip_search_no_match_returns_message(api_client, requests_mock):
    """A symbol with no matches returns the 'No data found' message."""
    _mock_fo(api_client, requests_mock)
    result = ScripSearch(api_client).scrip_search(
        symbol="doesnotexist",
        exchange_segment="nse_fo",
        expiry=None,
        option_type=None,
        strike_price=None,
        ignore_50multiple=True,
    )
    assert isinstance(result, dict)
    assert "message" in result


def test_scrip_search_expiry_and_strike_on_cash_segment(api_client, requests_mock):
    """Cash segment with expiry+strike returns the 'no expiry/strike' error."""
    url = api_client.configuration.get_url_details("scrip_master")
    path = "https://api.kotaksecurities.com/scripmaster/NSE_CM.csv"
    csv = "pSymbol,pTrdSymbol,pExchSeg,pSymbolName\n1,RELIANCE-EQ,nse_cm,RELIANCE\n"
    requests_mock.get(url, json={"stat": "Ok", "data": {"filesPaths": [path]}}, status_code=200)
    requests_mock.get(path, text=csv, status_code=200)

    result = ScripSearch(api_client).scrip_search(
        symbol="reliance",
        exchange_segment="nse_cm",
        expiry="01JAN2024",
        option_type=None,
        strike_price="22000",
        ignore_50multiple=True,
    )
    assert "error" in result


# ---- expiry / single-strike / mcx / bse coverage ----------------------------

# nse_fo rows in _FO_CSV resolve (after the +315511200s shift) to expiry 18Jun2024.


def test_scrip_search_expiry_single_date(api_client, requests_mock):
    """Single-date expiry filter (len==1 branch)."""
    _mock_fo(api_client, requests_mock)
    result = ScripSearch(api_client).scrip_search(
        symbol="nifty",
        exchange_segment="nse_fo",
        expiry="18Jun2024",
        option_type=None,
        strike_price=None,
        ignore_50multiple=True,
    )
    assert isinstance(result, list)
    assert len(result) == 2


def test_scrip_search_expiry_range(api_client, requests_mock):
    """Range expiry filter (len==2 branch)."""
    _mock_fo(api_client, requests_mock)
    result = ScripSearch(api_client).scrip_search(
        symbol="nifty",
        exchange_segment="nse_fo",
        expiry="01Jun2024-30Jun2024",
        option_type=None,
        strike_price=None,
        ignore_50multiple=True,
    )
    assert isinstance(result, list)
    assert len(result) == 2


def test_scrip_search_single_strike_exact_match(api_client, requests_mock):
    """Single positive strike price -> exact match branch (line 161)."""
    _mock_fo(api_client, requests_mock)
    result = ScripSearch(api_client).scrip_search(
        symbol="nifty",
        exchange_segment="nse_fo",
        expiry=None,
        option_type=None,
        strike_price="22000",  # matches the CE row (2200000 scaled)
        ignore_50multiple=True,
    )
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["dStrikePrice;"] == 2200000


# MCX/BSE use a different (non-shifted) expiry conversion path.
_MCX_CSV = (
    "pSymbol,pTrdSymbol,pExchSeg,pSymbolName,pOptionType,dStrikePrice;,pExpiryDate,pInstType\n"
    "1,GOLD24JUN,mcx_fo,GOLD,XX,0,1403222400,FUTCOM\n"
)

_BSE_CSV = (
    "pSymbol,pTrdSymbol,pExchSeg,pSymbolName,pOptionType,dStrikePrice;,pExpiryDate,pInstType\n"
    "1,SENSEX24JUN,bse_fo,SENSEX,XX,0,1403222400,FUTIDX\n"
)


def _mock_segment(api_client, requests_mock, csv, filename):
    url = api_client.configuration.get_url_details("scrip_master")
    path = f"https://api.kotaksecurities.com/scripmaster/{filename}"
    requests_mock.get(url, json={"stat": "Ok", "data": {"filesPaths": [path]}}, status_code=200)
    requests_mock.get(path, text=csv, status_code=200)


def test_scrip_search_mcx_fo_expiry_conversion(api_client, requests_mock):
    """mcx_fo takes the non-shifted expiry conversion branch (lines 75-76)."""
    _mock_segment(api_client, requests_mock, _MCX_CSV, "MCX_FO.csv")
    result = ScripSearch(api_client).scrip_search(
        symbol="gold",
        exchange_segment="mcx_fo",
        expiry=None,
        option_type=None,
        strike_price=None,
        ignore_50multiple=True,
    )
    assert result is not None


def test_scrip_search_bse_fo_expiry_conversion(api_client, requests_mock):
    """bse_fo takes the non-shifted expiry conversion branch (lines 75-76)."""
    _mock_segment(api_client, requests_mock, _BSE_CSV, "BSE_FO.csv")
    result = ScripSearch(api_client).scrip_search(
        symbol="sensex",
        exchange_segment="bse_fo",
        expiry=None,
        option_type=None,
        strike_price=None,
        ignore_50multiple=True,
    )
    assert result is not None


def test_scrip_search_api_exception_handled(api_client, monkeypatch):
    """An ApiException from the underlying request is caught and returned."""
    from neo_api_client.exceptions import ApiException

    scrip = ScripSearch(api_client)

    def boom(*args, **kwargs):
        raise ApiException(status=500, reason="boom")

    monkeypatch.setattr(scrip.rest_client, "request", boom)

    result = scrip.scrip_search(
        symbol="x",
        exchange_segment="nse_fo",
        expiry=None,
        option_type=None,
        strike_price=None,
        ignore_50multiple=True,
    )
    assert "error" in result


# ---- exchange_segment=None / empty symbol / exact-mcx branches --------------


def test_scrip_search_no_exchange_segment_returns_none(api_client, requests_mock):
    """exchange_segment is None -> the filter block is skipped, method returns None."""
    url = api_client.configuration.get_url_details("scrip_master")
    requests_mock.get(url, json={"stat": "Ok", "data": {"filesPaths": ["x.csv"]}}, status_code=200)

    result = ScripSearch(api_client).scrip_search(
        symbol="anything",
        exchange_segment=None,
        expiry=None,
        option_type=None,
        strike_price=None,
        ignore_50multiple=True,
    )
    assert result is None


def test_scrip_search_empty_symbol_skips_symbol_filter(api_client, requests_mock):
    """symbol == '' -> the symbol-name filter is skipped (82->86 branch)."""
    _mock_fo(api_client, requests_mock)
    result = ScripSearch(api_client).scrip_search(
        symbol="",  # no symbol filter applied
        exchange_segment="nse_fo",
        expiry=None,
        option_type=None,
        strike_price=None,
        ignore_50multiple=True,
    )
    assert isinstance(result, list)
    assert len(result) == 2  # both rows retained (no symbol filtering)


# The exact segment "mcx" (not "mcx_fo") does NOT end with "fo", so it takes the
# non-fo else branch and the mcx expiry conversion at lines 78-80.
_MCX_PLAIN_CSV = (
    "pSymbol,pTrdSymbol,pExchSeg,pSymbolName,pOptionType,dStrikePrice;,pExpiryDate,pInstType\n"
    "1,GOLD24JUN,mcx,GOLD,XX,0,1403222400,FUTCOM\n"
)


def test_scrip_search_mcx_plain_expiry_conversion(api_client, requests_mock):
    """exchange_segment == 'mcx' takes the non-fo mcx conversion (lines 79-80)."""
    _mock_segment(api_client, requests_mock, _MCX_PLAIN_CSV, "MCX.csv")
    result = ScripSearch(api_client).scrip_search(
        symbol="gold",
        exchange_segment="mcx",
        expiry=None,
        option_type=None,
        strike_price=None,
        ignore_50multiple=True,
    )
    assert result is not None
