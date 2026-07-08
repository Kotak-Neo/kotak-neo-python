# tests/unit/test_rest_exceptions.py

import httpx
import pytest

from neo_api_client.exceptions import ApiException


def test_timeout(api_client, monkeypatch):
    def fake_request(*args, **kwargs):
        raise httpx.TimeoutException("timed out")

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
        raise httpx.ConnectError("no route")

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
