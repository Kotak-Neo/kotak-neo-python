# tests/unit/test_rest_exceptions.py

import pytest
import requests

from neo_api_client.exceptions import ApiException


def test_timeout(api_client, monkeypatch):
    def fake_request(*args, **kwargs):
        raise requests.exceptions.Timeout()

    monkeypatch.setattr(
        api_client.rest_client.session,
        "request",
        fake_request,
    )

    with pytest.raises(ApiException):
        api_client.rest_client.request(
            method="GET",
            url="https://test.com",
        )


def test_connection_error(api_client, monkeypatch):
    def fake_request(*args, **kwargs):
        raise requests.exceptions.ConnectionError()

    monkeypatch.setattr(
        api_client.rest_client.session,
        "request",
        fake_request,
    )

    with pytest.raises(ApiException):
        api_client.rest_client.request(
            method="GET",
            url="https://test.com",
        )
