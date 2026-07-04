"""Additional coverage tests for RESTClientObject branches."""

import pytest
import requests
import requests_mock

from neo_api_client import rest as rest_module
from neo_api_client.exceptions import ApiException
from neo_api_client.rest import RESTClientObject


class DummyConfig:
    consumer_key = "abcdef1234567890"


# ---- HTTP method validation -------------------------------------------------


def test_unsupported_method_raises_value_error():
    client = RESTClientObject(DummyConfig())
    with pytest.raises(ValueError, match="Unsupported HTTP method"):
        client.request(method="FETCH", url="https://test.com")


# ---- Content-Type handling --------------------------------------------------


def test_invalid_content_type_raises_api_exception():
    client = RESTClientObject(DummyConfig())
    with pytest.raises(ApiException) as exc_info:
        client.request(
            method="POST",
            url="https://test.com",
            headers={"Content-Type": "text/plain"},
            body={"a": 1},
        )
    assert "Invalid Content-Type" in str(exc_info.value.reason)


def test_form_urlencoded_body_sent_as_jdata():
    client = RESTClientObject(DummyConfig())
    with requests_mock.Mocker() as m:
        m.post("https://test.com", json={"ok": True})
        resp = client.request(
            method="POST",
            url="https://test.com",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            body={"symbol": "RELIANCE"},
        )
        assert resp.status_code == 200
        # Body is form-encoded under a jData key.
        assert "jData" in m.last_request.text


# ---- Generic RequestException handler --------------------------------------


def test_generic_request_exception_wrapped(monkeypatch):
    client = RESTClientObject(DummyConfig())

    def boom(*args, **kwargs):
        raise requests.exceptions.RequestException("kaboom")

    monkeypatch.setattr(client.session, "request", boom)

    with pytest.raises(ApiException) as exc_info:
        client.request(method="GET", url="https://test.com")
    assert "kaboom" in str(exc_info.value.reason)


# ---- raise_on_error + _handle_error_response -------------------------------


def test_raise_on_error_json_body():
    client = RESTClientObject(DummyConfig(), raise_on_error=True)
    with requests_mock.Mocker() as m:
        m.get("https://test.com", json={"msg": "bad"}, status_code=400, reason="Bad Request")
        with pytest.raises(ApiException) as exc_info:
            client.request(method="GET", url="https://test.com")
    assert exc_info.value.status == 400
    assert exc_info.value.body == {"msg": "bad"}


def test_raise_on_error_text_body_fallback():
    client = RESTClientObject(DummyConfig(), raise_on_error=True)
    with requests_mock.Mocker() as m:
        # Non-JSON body -> falls back to text.
        m.get("https://test.com", text="Internal Error", status_code=500, reason="Server Error")
        with pytest.raises(ApiException) as exc_info:
            client.request(method="GET", url="https://test.com")
    assert exc_info.value.status == 500
    assert exc_info.value.body == "Internal Error"


def test_no_raise_on_error_returns_response():
    """Default (raise_on_error=False) returns the 4xx response without raising."""
    client = RESTClientObject(DummyConfig())
    with requests_mock.Mocker() as m:
        m.get("https://test.com", json={"msg": "bad"}, status_code=400)
        resp = client.request(method="GET", url="https://test.com")
    assert resp.status_code == 400


# ---- Rate limiter paths -----------------------------------------------------


class _FakeRateLimiter:
    def __init__(self, raise_timeout=False):
        self.raise_timeout = raise_timeout
        self.acquired = False

    def acquire(self, timeout=None):
        if self.raise_timeout:
            raise TimeoutError("rate limited")
        self.acquired = True

    def get_status(self):
        return {"available": 5}


def test_rate_limiter_acquire_called(monkeypatch):
    monkeypatch.setattr(rest_module, "_ENHANCED_FEATURES", True)
    client = RESTClientObject(DummyConfig())
    limiter = _FakeRateLimiter()
    client.rate_limiter = limiter

    with requests_mock.Mocker() as m:
        m.get("https://test.com", json={"ok": True})
        client.request(method="GET", url="https://test.com")

    assert limiter.acquired is True


def test_rate_limiter_timeout_raises_429(monkeypatch):
    monkeypatch.setattr(rest_module, "_ENHANCED_FEATURES", True)
    client = RESTClientObject(DummyConfig())
    client.rate_limiter = _FakeRateLimiter(raise_timeout=True)

    with pytest.raises(ApiException) as exc_info:
        client.request(method="GET", url="https://test.com")
    assert exc_info.value.status == 429


def test_get_rate_limit_status_with_limiter():
    client = RESTClientObject(DummyConfig())
    client.rate_limiter = _FakeRateLimiter()
    status = client.get_rate_limit_status()
    assert status == {"available": 5}


def test_get_rate_limit_status_without_limiter():
    client = RESTClientObject(DummyConfig())
    assert client.get_rate_limit_status() is None


# ---- close() ----------------------------------------------------------------


def test_close_is_idempotent():
    client = RESTClientObject(DummyConfig())
    client.close()
    # Second close must not raise.
    client.close()


# ---- URL sanitization -------------------------------------------------------


def test_sanitize_url_masks_sensitive_params():
    client = RESTClientObject(DummyConfig())
    sanitized = client._sanitize_url_for_logging("https://x/y?token=secret123&sid=abc&foo=bar")
    assert "secret123" not in sanitized
    assert "token=***" in sanitized
    assert "sid=***" in sanitized
    assert "foo=bar" in sanitized


# ---- Rate-limiting-enabled construction & close logging ---------------------


def test_init_with_rate_limiting_enabled(monkeypatch):
    """Constructing with enable_rate_limiting=True wires up a limiter + logs."""
    monkeypatch.setattr(rest_module, "_ENHANCED_FEATURES", True)
    monkeypatch.setattr(rest_module, "get_rate_limiter", lambda: _FakeRateLimiter(), raising=False)

    client = RESTClientObject(DummyConfig(), enable_rate_limiting=True)
    assert client.rate_limiter is not None


def test_close_logs_when_enhanced(monkeypatch):
    """close() takes the logging branch when enhanced features are on."""
    monkeypatch.setattr(rest_module, "_ENHANCED_FEATURES", True)
    client = RESTClientObject(DummyConfig())
    client.close()  # should log 'rest_client_closing' and close the session
    assert client.session is not None  # session object still present after close
