import os
import sys
import types

# Must run before the first `neo_api_client` import below: neo_api_client.logger
# reads NEO_LOG_FILE_ENABLED at import time to decide whether to create a
# rotating log file. Default it off for the test session so `pytest` doesn't
# write logs/neo_api_client.log into the repo; setdefault() still lets a
# developer override it explicitly to exercise the real file-logging path.
os.environ.setdefault("NEO_LOG_FILE_ENABLED", "false")

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


@pytest.fixture(autouse=True)
def _isolate_scrip_cache(tmp_path, monkeypatch):
    """Give every test its own scrip-master CSV cache directory.

    Without this, tests that mock different CSV content for the same
    exchange_segment (e.g. "nse_cm") would leak cached files into each other
    via the real on-disk cache used by search_scrip().
    """
    monkeypatch.setenv("NEO_SCRIP_CACHE_DIR", str(tmp_path / "scrip_cache"))


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
