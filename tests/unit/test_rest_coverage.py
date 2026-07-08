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


def test_rate_limiter_timeout_without_sanitizer_still_raises_429(monkeypatch):
    """Timeout path when _sanitize_url_for_logging is absent (168->170 branch)."""
    monkeypatch.setattr(rest_module, "_ENHANCED_FEATURES", True)
    client = RESTClientObject(DummyConfig())
    client.rate_limiter = _FakeRateLimiter(raise_timeout=True)
    # Remove the method from the class so hasattr(self, ...) is False -> skip the
    # log branch but still raise the 429.
    monkeypatch.delattr(type(client), "_sanitize_url_for_logging")

    with pytest.raises(ApiException) as exc_info:
        client.request(method="GET", url="https://test.com")
    assert exc_info.value.status == 429


def test_handle_error_response_without_enhanced_features(monkeypatch):
    """_handle_error_response with enhanced features off skips logging (319->327)."""
    monkeypatch.setattr(rest_module, "_ENHANCED_FEATURES", False)
    client = RESTClientObject(DummyConfig())

    with requests_mock.Mocker() as m:
        m.get("https://test.com", json={"msg": "bad"}, status_code=400, reason="Bad Request")
        resp = client.session.get("https://test.com")

    with pytest.raises(ApiException) as exc_info:
        client._handle_error_response(resp, request_id="rid-1")
    assert exc_info.value.status == 400


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


# ---- UAT X-Forwarded-For header ---------------------------------------------


class _EnvConfig:
    """Config stub exposing host + uat_x_forwarded_for like NeoUtility."""

    consumer_key = None

    def __init__(self, host, xff=None):
        self.host = host
        self.uat_x_forwarded_for = xff


# ---- Enhanced-features tracing / logging branches ---------------------------


def _enable_enhanced(monkeypatch):
    """Turn on _ENHANCED_FEATURES with a real logger so the tracing branches run."""
    from neo_api_client.logger import get_logger

    monkeypatch.setattr(rest_module, "_ENHANCED_FEATURES", True)
    monkeypatch.setattr(rest_module, "logger", get_logger("test_rest"), raising=False)


def test_enhanced_success_adds_tracing_headers_and_logs(monkeypatch):
    """With enhanced features on, request_id + client-id headers are attached
    and the success path logs (covers the request_id/start_time branches)."""
    _enable_enhanced(monkeypatch)
    client = RESTClientObject(DummyConfig())

    with requests_mock.Mocker() as m:
        m.get("https://test.com", json={"ok": True})
        resp = client.request(method="GET", url="https://test.com")

    assert resp.status_code == 200
    assert m.last_request.headers.get("X-Request-ID")
    # consumer_key is truthy on DummyConfig -> X-Client-ID is added (masked).
    assert m.last_request.headers.get("X-Client-ID", "").endswith("***")


def test_enhanced_timeout_logs_and_wraps(monkeypatch):
    _enable_enhanced(monkeypatch)
    client = RESTClientObject(DummyConfig())

    def boom(*a, **k):
        raise requests.exceptions.Timeout("slow")

    monkeypatch.setattr(client.session, "request", boom)
    with pytest.raises(ApiException) as exc_info:
        client.request(method="GET", url="https://test.com")
    assert "timeout" in str(exc_info.value.reason).lower()


def test_enhanced_connection_error_logs_and_wraps(monkeypatch):
    _enable_enhanced(monkeypatch)
    client = RESTClientObject(DummyConfig())

    def boom(*a, **k):
        raise requests.exceptions.ConnectionError("no route")

    monkeypatch.setattr(client.session, "request", boom)
    with pytest.raises(ApiException) as exc_info:
        client.request(method="GET", url="https://test.com")
    assert "Unable to connect" in str(exc_info.value.reason)


def test_enhanced_generic_request_exception_logs_and_wraps(monkeypatch):
    _enable_enhanced(monkeypatch)
    client = RESTClientObject(DummyConfig())

    def boom(*a, **k):
        raise requests.exceptions.RequestException("weird")

    monkeypatch.setattr(client.session, "request", boom)
    with pytest.raises(ApiException) as exc_info:
        client.request(method="GET", url="https://test.com")
    assert "weird" in str(exc_info.value.reason)


def test_enhanced_error_response_raises_via_handler(monkeypatch):
    """raise_on_error + enhanced features: _handle_error_response logs + raises."""
    _enable_enhanced(monkeypatch)
    client = RESTClientObject(DummyConfig(), raise_on_error=True)

    with requests_mock.Mocker() as m:
        m.get("https://test.com", json={"msg": "bad"}, status_code=400, reason="Bad Request")
        with pytest.raises(ApiException) as exc_info:
            client.request(method="GET", url="https://test.com")
    assert exc_info.value.status == 400


# ---- Enhanced-features DISABLED branches ------------------------------------
# _ENHANCED_FEATURES is True by default in this environment; these tests force
# it off to cover the "no tracing / no logging" arcs of the request paths.


def test_disabled_success_skips_tracing(monkeypatch):
    monkeypatch.setattr(rest_module, "_ENHANCED_FEATURES", False)
    client = RESTClientObject(DummyConfig())

    with requests_mock.Mocker() as m:
        m.get("https://test.com", json={"ok": True})
        resp = client.request(method="GET", url="https://test.com")

    assert resp.status_code == 200
    # No tracing header attached when enhanced features are off.
    assert "X-Request-ID" not in m.last_request.headers


def test_disabled_timeout_wraps_without_logging(monkeypatch):
    monkeypatch.setattr(rest_module, "_ENHANCED_FEATURES", False)
    client = RESTClientObject(DummyConfig())

    def boom(*a, **k):
        raise requests.exceptions.Timeout("slow")

    monkeypatch.setattr(client.session, "request", boom)
    with pytest.raises(ApiException):
        client.request(method="GET", url="https://test.com")


def test_disabled_connection_error_wraps_without_logging(monkeypatch):
    monkeypatch.setattr(rest_module, "_ENHANCED_FEATURES", False)
    client = RESTClientObject(DummyConfig())

    def boom(*a, **k):
        raise requests.exceptions.ConnectionError("no route")

    monkeypatch.setattr(client.session, "request", boom)
    with pytest.raises(ApiException):
        client.request(method="GET", url="https://test.com")


def test_disabled_generic_exception_wraps_without_logging(monkeypatch):
    monkeypatch.setattr(rest_module, "_ENHANCED_FEATURES", False)
    client = RESTClientObject(DummyConfig())

    def boom(*a, **k):
        raise requests.exceptions.RequestException("weird")

    monkeypatch.setattr(client.session, "request", boom)
    with pytest.raises(ApiException):
        client.request(method="GET", url="https://test.com")


def test_disabled_error_response_not_raised(monkeypatch):
    """raise_on_error requires _ENHANCED_FEATURES; disabled -> 4xx returned as-is."""
    monkeypatch.setattr(rest_module, "_ENHANCED_FEATURES", False)
    client = RESTClientObject(DummyConfig(), raise_on_error=True)

    with requests_mock.Mocker() as m:
        m.get("https://test.com", json={"msg": "bad"}, status_code=400)
        resp = client.request(method="GET", url="https://test.com")
    assert resp.status_code == 400


def test_disabled_close_skips_log(monkeypatch):
    """close() with enhanced features off skips the logging branch."""
    monkeypatch.setattr(rest_module, "_ENHANCED_FEATURES", False)
    client = RESTClientObject(DummyConfig())
    client.close()  # must not raise; session still present
    assert client.session is not None


def test_close_with_no_session_is_noop():
    """close() short-circuits when there is no session (348 -> exit)."""
    client = RESTClientObject(DummyConfig())
    client.session = None
    client.close()  # must not raise


def test_close_log_failure_is_suppressed(monkeypatch):
    """A failing close-log must not prevent session.close() (353-354)."""
    _enable_enhanced(monkeypatch)
    client = RESTClientObject(DummyConfig())

    def boom(*a, **k):
        raise RuntimeError("logging down")

    monkeypatch.setattr(rest_module.logger, "info", boom)
    client.close()  # exception suppressed; still closes cleanly
    assert client.session is not None


def test_uat_sets_x_forwarded_for_header():
    client = RESTClientObject(_EnvConfig("uat", "10.1.2.3"))
    with requests_mock.Mocker() as m:
        m.get("https://test.com", json={})
        client.request(method="GET", url="https://test.com")
        assert m.last_request.headers.get("X-Forwarded-For") == "10.1.2.3"


def test_prod_does_not_set_x_forwarded_for():
    client = RESTClientObject(_EnvConfig("prod", "10.1.2.3"))
    with requests_mock.Mocker() as m:
        m.get("https://test.com", json={})
        client.request(method="GET", url="https://test.com")
        assert "X-Forwarded-For" not in m.last_request.headers


def test_uat_without_value_does_not_set_header():
    client = RESTClientObject(_EnvConfig("uat", None))
    with requests_mock.Mocker() as m:
        m.get("https://test.com", json={})
        client.request(method="GET", url="https://test.com")
        assert "X-Forwarded-For" not in m.last_request.headers


def test_explicit_x_forwarded_for_header_not_overwritten():
    client = RESTClientObject(_EnvConfig("uat", "10.1.2.3"))
    with requests_mock.Mocker() as m:
        m.get("https://test.com", json={})
        client.request(
            method="GET",
            url="https://test.com",
            headers={"X-Forwarded-For": "9.9.9.9"},
        )
        assert m.last_request.headers.get("X-Forwarded-For") == "9.9.9.9"
