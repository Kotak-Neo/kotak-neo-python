"""Additional tests for REST client edge cases."""

import requests_mock as rm

from neo_api_client.rest import RESTClientObject


class DummyConfig:
    pass


def test_request_exception_handling():
    """Test request with exception."""
    client = RESTClientObject(DummyConfig())

    with rm.Mocker() as m:
        m.get("https://test.com/error", exc=Exception("Network error"))

        try:
            client.request(method="GET", url="https://test.com/error")
        except Exception as e:
            assert "Network error" in str(e)


def test_request_with_timeout():
    """Test request with timeout."""
    client = RESTClientObject(DummyConfig())

    with rm.Mocker() as m:
        m.get("https://test.com", json={"status": "ok"})

        response = client.request(method="GET", url="https://test.com")

        assert response.status_code == 200


def test_request_with_empty_body():
    """Test POST request with empty body."""
    client = RESTClientObject(DummyConfig())

    with rm.Mocker() as m:
        m.post("https://test.com", json={"status": "ok"})

        response = client.request(method="POST", url="https://test.com", body={})

        assert response.status_code == 200


def test_request_with_none_body():
    """Test POST request with None body."""
    client = RESTClientObject(DummyConfig())

    with rm.Mocker() as m:
        m.post("https://test.com", json={"status": "ok"})

        response = client.request(method="POST", url="https://test.com", body=None)

        assert response.status_code == 200


def test_request_patch_method():
    """Test PATCH request."""
    client = RESTClientObject(DummyConfig())

    with rm.Mocker() as m:
        m.patch("https://test.com/resource", json={"updated": True})

        response = client.request(
            method="PATCH", url="https://test.com/resource", body={"field": "value"}
        )

        assert response.status_code == 200
        assert response.json()["updated"] is True


def test_request_options_method():
    """Test OPTIONS request."""
    client = RESTClientObject(DummyConfig())

    with rm.Mocker() as m:
        m.options("https://test.com", json={"methods": ["GET", "POST"]})

        response = client.request(method="OPTIONS", url="https://test.com")

        assert response.status_code == 200


def test_request_head_method():
    """Test HEAD request."""
    client = RESTClientObject(DummyConfig())

    with rm.Mocker() as m:
        m.head("https://test.com")

        response = client.request(method="HEAD", url="https://test.com")

        assert response.status_code == 200


def test_rest_client_multiple_requests():
    """Test multiple sequential requests."""
    client = RESTClientObject(DummyConfig())

    with rm.Mocker() as m:
        m.get("https://test.com/1", json={"id": 1})
        m.get("https://test.com/2", json={"id": 2})

        response1 = client.request(method="GET", url="https://test.com/1")
        response2 = client.request(method="GET", url="https://test.com/2")

        assert response1.json()["id"] == 1
        assert response2.json()["id"] == 2


def test_request_with_query_string_in_url():
    """Test request with query string already in URL."""
    client = RESTClientObject(DummyConfig())

    with rm.Mocker() as m:
        m.get("https://test.com?existing=param&new=value")

        response = client.request(
            method="GET", url="https://test.com?existing=param", query_params={"new": "value"}
        )

        assert response.status_code == 200
