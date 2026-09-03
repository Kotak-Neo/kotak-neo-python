"""Unit tests for NeoUtility class."""

import pytest

from neo_api_client.__version__ import __version__
from neo_api_client.exceptions import ApiValueError
from neo_api_client.rest import RESTClientObject
from neo_api_client.utils.neo_utility import NeoUtility
from neo_api_client.utils.urls import CONFIG_SERVICE_URL_PROD, CONFIG_SERVICE_URL_UAT


def test_neo_utility_init():
    """Test NeoUtility initialization."""
    utility = NeoUtility(
        host="prod",
        access_token="test_token",
        neo_fin_key="test_fin_key",
        consumer_key="test_consumer_key",
    )

    assert utility.host == "prod"
    assert utility.bearer_token == "test_token"
    assert utility.neo_fin_key == "test_fin_key"
    assert utility.consumer_key == "test_consumer_key"
    assert utility.view_token is None
    assert utility.sid is None
    assert utility.userId is None


def test_neo_utility_init_minimal():
    """Test NeoUtility initialization with minimal parameters."""
    utility = NeoUtility(host="uat")

    assert utility.host == "uat"
    assert utility.bearer_token is None
    assert utility.neo_fin_key is None


def test_extract_userid_success():
    """Test extracting user ID from JWT token."""
    utility = NeoUtility(host="prod")
    # Valid JWT token with sub claim (must have valid signature part)
    # This is a properly formatted JWT: header.payload.signature
    # Payload decoded: {"sub": "TEST_USER"}
    test_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJURVNUX1VTRVIifQ.4Adcj0vVzY1tGwWvxpTKkFtPBpAlhTC5R-Vhk-F_yOs"

    user_id = utility.extract_userid(test_token)

    assert user_id == "TEST_USER"
    assert utility.userId == "TEST_USER"


def test_extract_userid_no_token():
    """Test extract_userid raises error when token is None."""
    utility = NeoUtility(host="prod")

    with pytest.raises(ApiValueError) as exc_info:
        utility.extract_userid(None)

    assert "View Token hasn't been Generated" in str(exc_info.value)


def test_extract_userid_empty_token():
    """Test extract_userid raises error when token is empty."""
    utility = NeoUtility(host="prod")

    with pytest.raises(ApiValueError) as exc_info:
        utility.extract_userid("")

    assert "View Token hasn't been Generated" in str(exc_info.value)


def test_get_domain_prod_session_init():
    """Test get_domain for prod with session_init=True."""
    utility = NeoUtility(host="prod")

    domain = utility.get_domain(session_init=True)

    assert domain == "https://mis.kotaksecurities.com"


def test_get_domain_prod_normal():
    """Test get_domain for prod with session_init=False."""
    utility = NeoUtility(host="prod")
    utility.base_url = "https://e21.kotaksecurities.com"

    domain = utility.get_domain(session_init=False)

    assert domain == "https://e21.kotaksecurities.com"


def test_get_domain_uat_session_init():
    """Test get_domain for UAT with session_init=True."""
    utility = NeoUtility(host="uat")

    domain = utility.get_domain(session_init=True)

    assert domain == "https://d-mis.kotaksecurities.com"


def test_get_domain_uat_normal():
    """Test get_domain for UAT with session_init=False."""
    utility = NeoUtility(host="uat")

    domain = utility.get_domain(session_init=False)

    # For UAT without session_init, it uses UAT_BASE_URL
    assert domain == "https://d-mis.kotaksecurities.com"


def test_get_domain_invalid_host():
    """Test get_domain raises error for invalid host."""
    utility = NeoUtility(host="invalid")

    with pytest.raises(ApiValueError) as exc_info:
        utility.get_domain()

    assert "Invalid environment specified" in str(exc_info.value)


def test_get_domain_case_insensitive():
    """Test get_domain handles case-insensitive host."""
    utility = NeoUtility(host="PROD")

    domain = utility.get_domain(session_init=True)

    assert domain == "https://mis.kotaksecurities.com"


def test_get_url_details_prod():
    """Test get_url_details for prod environment."""
    utility = NeoUtility(host="prod")
    utility.base_url = "https://e21.kotaksecurities.com"

    url = utility.get_url_details("limits")

    # PROD_URL for limits is "quick/user/limits"
    assert url == "https://e21.kotaksecurities.com/quick/user/limits"


def test_get_url_details_uat():
    """Test get_url_details for UAT environment."""
    utility = NeoUtility(host="uat")

    url = utility.get_url_details("limits")

    # UAT_URL for limits is "quick/user/limits"
    assert url == "https://d-mis.kotaksecurities.com/quick/user/limits"


def test_get_url_details_invalid_api():
    """Test get_url_details raises error for invalid api_info."""
    utility = NeoUtility(host="prod")
    utility.base_url = "https://e21.kotaksecurities.com"

    with pytest.raises(ValueError) as exc_info:
        utility.get_url_details("invalid_api")

    assert "Endpoint mapping not found" in str(exc_info.value)


def test_get_url_details_missing_base_url_raises(monkeypatch):
    """When the domain can't be resolved, get_url_details raises a clear error."""
    utility = NeoUtility(host="prod")
    # Force get_domain to yield nothing (e.g. base URL not configured yet).
    monkeypatch.setattr(utility, "get_domain", lambda: None)

    with pytest.raises(ValueError) as exc_info:
        utility.get_url_details("limits")

    assert "Base URL is not configured" in str(exc_info.value)


def test_get_neo_fin_key_prod_default():
    """Test get_neo_fin_key returns default for prod."""
    utility = NeoUtility(host="prod")

    fin_key = utility.get_neo_fin_key()

    assert fin_key == "neotradeapi"


def test_get_neo_fin_key_prod_custom():
    """Test get_neo_fin_key returns custom key for prod."""
    utility = NeoUtility(host="prod", neo_fin_key="custom_key")

    fin_key = utility.get_neo_fin_key()

    assert fin_key == "custom_key"


def test_get_neo_fin_key_uat_default():
    """Test get_neo_fin_key returns the same default ('neotradeapi') for UAT."""
    utility = NeoUtility(host="uat")

    fin_key = utility.get_neo_fin_key()

    assert fin_key == "neotradeapi"


def test_get_neo_fin_key_uat_custom():
    """Test get_neo_fin_key returns custom key for UAT."""
    utility = NeoUtility(host="uat", neo_fin_key="custom_uat_key")

    fin_key = utility.get_neo_fin_key()

    assert fin_key == "custom_uat_key"


def test_neo_utility_attributes_mutable():
    """Test that NeoUtility attributes can be set after initialization."""
    utility = NeoUtility(host="prod")

    utility.view_token = "view_123"
    utility.sid = "sid_123"
    utility.userId = "user_123"
    utility.edit_token = "edit_123"
    utility.edit_sid = "edit_sid_123"
    utility.edit_rid = "rid_123"
    utility.data_center = "DC1"
    utility.base_url = "https://custom.url"

    assert utility.view_token == "view_123"
    assert utility.sid == "sid_123"
    assert utility.userId == "user_123"
    assert utility.edit_token == "edit_123"
    assert utility.edit_sid == "edit_sid_123"
    assert utility.edit_rid == "rid_123"
    assert utility.data_center == "DC1"
    assert utility.base_url == "https://custom.url"


def test_resolve_dynamic_urls_uat_success(requests_mock):
    """Resolves via broadcast_source: E22_broadcast_source="ks" -> looks up
    E22_ks_broadcast_endpoint (SFeed) and E22_ks_interactive_endpoint (order feed)."""
    utility = NeoUtility(host="uat")
    utility.data_center = "E22"
    rest_client = RESTClientObject(utility)

    requests_mock.get(
        CONFIG_SERVICE_URL_UAT,
        json={
            "data": {
                "configs": {
                    "E22_broadcast_source": "ks",
                    "E22_ks_broadcast_endpoint": "https://uat.kotaksecurities.com/ufeed",
                    "E22_ks_interactive_endpoint": "https://uat.kotaksecurities.com/uinteractive",
                    # Present but must NOT be used, since broadcast_source is "ks", not "sh".
                    "E22_sh_broadcast_endpoint": "https://sfeed.kotaksecurities.com/apifeed",
                    "E22_sh_interactive_endpoint": "https://e22.kotaksecurities.com/realtime",
                }
            }
        },
    )

    utility.resolve_dynamic_urls(rest_client)

    assert utility.sfeed_websocket_url == "https://uat.kotaksecurities.com/ufeed"
    assert utility.order_feed_url == "https://uat.kotaksecurities.com/uinteractive"
    assert requests_mock.last_request.query["environment"] == "qa"
    assert requests_mock.last_request.query["platform"] == "api"
    assert requests_mock.last_request.query["appVersion"] == __version__


def test_resolve_dynamic_urls_order_feed_endpoint_missing_leaves_none(requests_mock):
    """Real-world shape: broadcast_source resolves and SFeed's key exists, but
    there's no matching *_interactive_endpoint for that broadcast_source -- e.g.
    E43_broadcast_source="ks" but only E43_ks_broadcast_endpoint is defined, not
    E43_ks_interactive_endpoint. order_feed_url must stay None in that case,
    independent of sfeed_websocket_url resolving fine."""
    utility = NeoUtility(host="uat")
    utility.data_center = "E43"
    rest_client = RESTClientObject(utility)

    requests_mock.get(
        CONFIG_SERVICE_URL_UAT,
        json={
            "data": {
                "configs": {
                    "E43_broadcast_source": "ks",
                    "E43_ks_broadcast_endpoint": "https://uat.kotaksecurities.com/ufeed",
                }
            }
        },
    )

    utility.resolve_dynamic_urls(rest_client)

    assert utility.sfeed_websocket_url == "https://uat.kotaksecurities.com/ufeed"
    assert utility.order_feed_url is None


def test_resolve_dynamic_urls_prod_uses_prod_config_service(requests_mock):
    """Prod queries the real prod config-service URL with environment=prod."""
    utility = NeoUtility(host="prod")
    utility.data_center = "E43"
    rest_client = RESTClientObject(utility)

    requests_mock.get(
        CONFIG_SERVICE_URL_PROD,
        json={
            "data": {
                "configs": {
                    "E43_broadcast_source": "ks",
                    "E43_ks_broadcast_endpoint": "https://uat.kotaksecurities.com/ufeed",
                }
            }
        },
    )

    utility.resolve_dynamic_urls(rest_client)

    assert utility.sfeed_websocket_url == "https://uat.kotaksecurities.com/ufeed"
    assert requests_mock.last_request.query["environment"] == "prod"


def test_resolve_dynamic_urls_no_broadcast_source_leaves_none(requests_mock):
    """No {data_center}_broadcast_source entry -> sfeed_websocket_url stays None (caller falls back)."""
    utility = NeoUtility(host="uat")
    utility.data_center = "E21"
    rest_client = RESTClientObject(utility)

    requests_mock.get(
        CONFIG_SERVICE_URL_UAT,
        json={
            "data": {
                # E21 has an sh_broadcast_endpoint but no broadcast_source key,
                # so it must not be picked up without going through that lookup.
                "configs": {
                    "E21_sh_broadcast_endpoint": "https://sfeed.kotaksecurities.com/apifeed"
                }
            }
        },
    )

    utility.resolve_dynamic_urls(rest_client)

    assert utility.sfeed_websocket_url is None


def test_resolve_dynamic_urls_broadcast_source_endpoint_missing_leaves_none(requests_mock):
    """broadcast_source resolves, but the constructed endpoint key isn't in the config."""
    utility = NeoUtility(host="uat")
    utility.data_center = "E22"
    rest_client = RESTClientObject(utility)

    requests_mock.get(
        CONFIG_SERVICE_URL_UAT,
        # E22_broadcast_source resolves to "ks", but E22_ks_broadcast_endpoint
        # itself is absent from this config.
        json={"data": {"configs": {"E22_broadcast_source": "ks"}}},
    )

    utility.resolve_dynamic_urls(rest_client)

    assert utility.sfeed_websocket_url is None


def test_resolve_dynamic_urls_request_failure_leaves_none(requests_mock):
    """A failed config-service call leaves sfeed_websocket_url as None instead of raising."""
    utility = NeoUtility(host="uat")
    utility.data_center = "E21"
    rest_client = RESTClientObject(utility)

    requests_mock.get(CONFIG_SERVICE_URL_UAT, exc=ConnectionError("boom"))

    utility.resolve_dynamic_urls(rest_client)

    assert utility.sfeed_websocket_url is None


def test_resolve_dynamic_urls_no_data_center_skips_request(requests_mock):
    """Without a data_center (e.g. before totp_validate), no request is made at all."""
    utility = NeoUtility(host="uat")
    rest_client = RESTClientObject(utility)

    utility.resolve_dynamic_urls(rest_client)

    assert utility.sfeed_websocket_url is None
    assert not requests_mock.called


def test_get_url_details_strips_slashes():
    """Test that get_url_details properly handles trailing/leading slashes."""
    utility = NeoUtility(host="prod")
    utility.base_url = "https://e21.kotaksecurities.com/"

    url = utility.get_url_details("limits")

    # Should not have double slashes
    assert "//" not in url.replace("https://", "")
    assert url == "https://e21.kotaksecurities.com/quick/user/limits"


def test_get_url_details_market_data_uses_base_url_when_available():
    """expiries/option_chain/historical_data route through get_url_details()
    like quotes()/scrip_master() -- once base_url is known (post
    totp_validate()), it resolves to the account's own data-center domain."""
    utility = NeoUtility(host="prod")
    utility.base_url = "https://e22.kotaksecurities.com"

    assert (
        utility.get_url_details("expiries")
        == "https://e22.kotaksecurities.com/market-data/1.0/watchlist/expiries"
    )
    assert (
        utility.get_url_details("option_chain")
        == "https://e22.kotaksecurities.com/market-data/1.0/watchlist/option-chain"
    )
    assert (
        utility.get_url_details("historical_data")
        == "https://e22.kotaksecurities.com/market-data/1.0/historical/details"
    )


def test_get_url_details_market_data_falls_back_without_base_url():
    """Without base_url (i.e. before totp_validate()), these still resolve
    -- via the shared gateway domain -- instead of raising, since the wire
    call itself only needs consumer_key."""
    utility = NeoUtility(host="prod")

    assert (
        utility.get_url_details("expiries")
        == "https://mis.kotaksecurities.com/market-data/1.0/watchlist/expiries"
    )
