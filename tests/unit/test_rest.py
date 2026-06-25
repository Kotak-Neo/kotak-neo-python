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
