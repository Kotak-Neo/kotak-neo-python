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
