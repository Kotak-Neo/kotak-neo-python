import httpx
import requests_mock

from neo_api_client.rest import RESTClientObject


class DummyConfig:
    pass


def test_get_request():
    client = RESTClientObject(DummyConfig())

    with requests_mock.Mocker() as m:
        m.get(
            "https://test.com",
            json={"status": "ok"},
        )

        response = client.request(
            method="GET",
            url="https://test.com",
        )

        assert response.status_code == 200
        assert response.json()["status"] == "ok"


def test_post_request():
    client = RESTClientObject(None)

    with requests_mock.Mocker() as mocker:
        mocker.post(
            "https://test.com",
            json={"order_id": "123"},
        )

        response = client.request(
            method="POST",
            url="https://test.com",
            body={"symbol": "SBIN"},
        )

        assert response.status_code == 200
        assert response.json()["order_id"] == "123"


def test_put_request():
    """Test PUT request."""
    client = RESTClientObject(DummyConfig())

    with requests_mock.Mocker() as m:
        m.put("https://test.com/order/123", json={"updated": True})

        response = client.request(
            method="PUT", url="https://test.com/order/123", body={"quantity": 10}
        )

        assert response.status_code == 200
        assert response.json()["updated"] is True


def test_delete_request():
    """Test DELETE request."""
    client = RESTClientObject(DummyConfig())

    with requests_mock.Mocker() as m:
        m.delete("https://test.com/order/123", json={"deleted": True})

        response = client.request(method="DELETE", url="https://test.com/order/123")

        assert response.status_code == 200
        assert response.json()["deleted"] is True


def test_request_with_headers():
    """Test request with custom headers."""
    client = RESTClientObject(DummyConfig())

    with requests_mock.Mocker() as m:
        m.get("https://test.com")

        response = client.request(
            method="GET",
            url="https://test.com",
            headers={"Authorization": "Bearer token", "Custom-Header": "value"},
        )

        assert response.status_code == 200


def test_request_with_params():
    """Test request with query parameters."""
    client = RESTClientObject(DummyConfig())

    with requests_mock.Mocker() as m:
        m.get("https://test.com?param1=value1&param2=value2")

        response = client.request(
            method="GET",
            url="https://test.com",
            query_params={"param1": "value1", "param2": "value2"},
        )

        assert response.status_code == 200


def test_rest_client_close():
    """Test REST client close method."""
    client = RESTClientObject(DummyConfig())

    # Should not raise exceptions
    client.close()


def test_rest_client_context_manager():
    """Test REST client as context manager."""
    with RESTClientObject(DummyConfig()) as client:
        assert client is not None

    # Client should be closed after exiting context


def test_custom_transport_is_used_by_session():
    """A custom transport is threaded straight through to the httpx.Client."""
    custom_transport = httpx.HTTPTransport()

    client = RESTClientObject(DummyConfig(), transport=custom_transport)

    assert client.session._transport is custom_transport


def test_custom_limits_applied_when_no_transport_given():
    """Custom pool limits reach the httpx.Client's default transport."""
    custom_limits = httpx.Limits(max_connections=5, max_keepalive_connections=2)

    client = RESTClientObject(DummyConfig(), limits=custom_limits)

    assert client.session._transport._pool._max_connections == 5


def test_default_session_unaffected_when_no_transport_or_limits_given():
    """Existing callers who don't pass transport/limits keep today's defaults."""
    client = RESTClientObject(DummyConfig())

    assert client.session._transport._pool._max_connections == 20


def test_http2_can_be_disabled():
    """http2=False is honored on the default transport."""
    client = RESTClientObject(DummyConfig(), http2=False)

    assert client.session._transport._pool._http2 is False


def test_http2_enabled_by_default():
    """Existing callers who don't pass http2 keep today's default (enabled)."""
    client = RESTClientObject(DummyConfig())

    assert client.session._transport._pool._http2 is True


def test_custom_timeout_applied_to_session():
    """A custom client-level timeout reaches the httpx.Client."""
    client = RESTClientObject(DummyConfig(), timeout=45)

    assert client.session.timeout.connect == 45


def test_default_timeout_unaffected_when_not_given():
    """Existing callers who don't pass timeout keep today's default (30s)."""
    client = RESTClientObject(DummyConfig())

    assert client.session.timeout.connect == 30


def test_per_call_timeout_overrides_client_level_timeout(monkeypatch):
    """The timeout kwarg on request() still overrides the client-level default."""
    client = RESTClientObject(DummyConfig(), timeout=45)
    captured = {}
    original_request = client.session.request

    def spy_request(method, **kwargs):
        captured["timeout"] = kwargs["timeout"]
        return original_request(method, **kwargs)

    monkeypatch.setattr(client.session, "request", spy_request)

    with requests_mock.Mocker() as m:
        m.get("https://test.com")

        response = client.request(method="GET", url="https://test.com", timeout=5)

        assert response.status_code == 200
        assert captured["timeout"] == 5
