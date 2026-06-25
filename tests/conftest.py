import pytest

from neo_api_client.api_client import ApiClient
from neo_api_client.utils.neo_utility import NeoUtility


@pytest.fixture
def api_client():
    utility = NeoUtility(
        host="prod",
        consumer_key="test_key",
    )

    utility.base_url = "https://test-api.kotak.com"
    utility.bearer_token = "dummy_token"
    utility.edit_token = "edit_token"
    utility.edit_sid = "edit_sid"
    utility.edit_rid = "edit_rid"

    return ApiClient(utility)
