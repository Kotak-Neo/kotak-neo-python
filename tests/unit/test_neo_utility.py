"""Unit tests for NeoUtility class."""

import pytest

from neo_api_client.exceptions import ApiValueError
from neo_api_client.utils.neo_utility import NeoUtility


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
    utility.base_url = "https://gw-napi.kotaksecurities.com"

    domain = utility.get_domain(session_init=False)

    assert domain == "https://gw-napi.kotaksecurities.com"


def test_get_domain_uat_session_init():
    """Test get_domain for UAT with session_init=True."""
    utility = NeoUtility(host="uat")

    domain = utility.get_domain(session_init=True)

    assert domain == "https://mis.kotaksecurities.com"


def test_get_domain_uat_normal():
    """Test get_domain for UAT with session_init=False."""
    utility = NeoUtility(host="uat")

    domain = utility.get_domain(session_init=False)

    # For UAT without session_init, it uses UAT_BASE_URL
    assert domain == "https://d-mis.kotaksecurities.com/"


def test_get_domain_invalid_host():
    """Test get_domain raises error for invalid host."""
    utility = NeoUtility(host="invalid")

    with pytest.raises(ApiValueError) as exc_info:
        utility.get_domain()

    assert "Either UAT or PROD in Environment accepted" in str(exc_info.value)


def test_get_domain_case_insensitive():
    """Test get_domain handles case-insensitive host."""
    utility = NeoUtility(host="PROD")

    domain = utility.get_domain(session_init=True)

    assert domain == "https://mis.kotaksecurities.com"


def test_get_url_details_prod():
    """Test get_url_details for prod environment."""
    utility = NeoUtility(host="prod")
    utility.base_url = "https://gw-napi.kotaksecurities.com"

    url = utility.get_url_details("limits")

    # PROD_URL for limits is "quick/user/limits"
    assert url == "https://gw-napi.kotaksecurities.com/quick/user/limits"


def test_get_url_details_uat():
    """Test get_url_details for UAT environment."""
    utility = NeoUtility(host="uat")

    url = utility.get_url_details("limits")

    # UAT_URL for limits is "orderapi/1.0/quick/user/limits"
    assert url == "https://d-mis.kotaksecurities.com/orderapi/1.0/quick/user/limits"


def test_get_url_details_invalid_api():
    """Test get_url_details raises error for invalid api_info."""
    utility = NeoUtility(host="prod")
    utility.base_url = "https://gw-napi.kotaksecurities.com"

    with pytest.raises(ValueError) as exc_info:
        utility.get_url_details("invalid_api")

    assert "Endpoint mapping not found" in str(exc_info.value)


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
    """Test get_neo_fin_key returns default for UAT."""
    utility = NeoUtility(host="uat")

    fin_key = utility.get_neo_fin_key()

    assert fin_key == "bQJNkL5z8m4aGcRgjDvXhHfSx7VpZnE"


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
    utility.serverId = "server_123"
    utility.data_center = "DC1"
    utility.base_url = "https://custom.url"

    assert utility.view_token == "view_123"
    assert utility.sid == "sid_123"
    assert utility.userId == "user_123"
    assert utility.edit_token == "edit_123"
    assert utility.edit_sid == "edit_sid_123"
    assert utility.edit_rid == "rid_123"
    assert utility.serverId == "server_123"
    assert utility.data_center == "DC1"
    assert utility.base_url == "https://custom.url"


def test_get_url_details_strips_slashes():
    """Test that get_url_details properly handles trailing/leading slashes."""
    utility = NeoUtility(host="prod")
    utility.base_url = "https://gw-napi.kotaksecurities.com/"

    url = utility.get_url_details("limits")

    # Should not have double slashes
    assert "//" not in url.replace("https://", "")
    assert url == "https://gw-napi.kotaksecurities.com/quick/user/limits"
