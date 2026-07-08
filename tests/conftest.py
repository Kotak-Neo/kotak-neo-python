import sys
import types

import pytest

from neo_api_client.api_client import ApiClient
from neo_api_client.utils.neo_utility import NeoUtility
from tests._httpmock import Mocker, RespxMock

# The SDK transport is httpx (HTTP/2), so the real `requests_mock` package no
# longer intercepts anything. Register a respx-backed stand-in under the same
# import name so `import requests_mock; requests_mock.Mocker()` keeps working.
if "requests_mock" not in sys.modules:
    _rm = types.ModuleType("requests_mock")
    _rm.Mocker = Mocker
    sys.modules["requests_mock"] = _rm


@pytest.fixture
def requests_mock():
    """respx-backed replacement for the pytest ``requests_mock`` fixture."""
    mock = RespxMock()
    mock.start()
    try:
        yield mock
    finally:
        mock.stop()


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
