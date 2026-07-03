"""Unit tests for retry logic."""

import pytest

from neo_api_client.exceptions import ApiException, ErrorCategory
from neo_api_client.retry import (
    RetryConfig,
    add_jitter,
    create_retry_decorator,
    should_retry_exception,
    with_retry,
)

# ---- should_retry_exception -------------------------------------------------


def test_should_retry_on_retryable_status_code():
    exc = ApiException(status=503, reason="Service Unavailable")
    assert should_retry_exception(exc) is True


def test_should_not_retry_on_non_retryable_status_code():
    exc = ApiException(status=400, reason="Bad Request")
    assert should_retry_exception(exc) is False


def test_should_retry_on_network_category():
    exc = ApiException(reason="conn")
    exc.status = None
    exc.category = ErrorCategory.NETWORK
    assert should_retry_exception(exc) is True


def test_should_retry_on_timeout_category():
    exc = ApiException(reason="timeout")
    exc.status = None
    exc.category = ErrorCategory.TIMEOUT
    assert should_retry_exception(exc) is True


def test_should_not_retry_on_validation_category():
    exc = ApiException(reason="bad")
    exc.status = None
    exc.category = ErrorCategory.VALIDATION
    assert should_retry_exception(exc) is False


def test_should_retry_on_requests_timeout():
    import requests.exceptions as req_exc

    assert should_retry_exception(req_exc.Timeout()) is True
    assert should_retry_exception(req_exc.ConnectionError()) is True


def test_should_not_retry_on_plain_exception():
    assert should_retry_exception(ValueError("nope")) is False


# ---- add_jitter -------------------------------------------------------------


def test_add_jitter_within_range():
    base = 5.0
    lo, hi = RetryConfig.JITTER_RANGE
    result = add_jitter(base)
    assert base + lo <= result <= base + hi


# ---- with_retry -------------------------------------------------------------


def test_with_retry_succeeds_first_try():
    calls = []

    @with_retry(max_attempts=3)
    def ok():
        calls.append(1)
        return "done"

    assert ok() == "done"
    assert len(calls) == 1


def test_with_retry_retries_then_succeeds(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda _s: None)
    attempts = {"n": 0}

    @with_retry(max_attempts=3, initial_wait=0.01, max_wait=0.02)
    def flaky():
        attempts["n"] += 1
        if attempts["n"] < 2:
            raise ApiException(status=503, reason="unavailable")
        return "recovered"

    assert flaky() == "recovered"
    assert attempts["n"] == 2


def test_with_retry_exhausts_and_raises(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda _s: None)
    attempts = {"n": 0}

    @with_retry(max_attempts=3, initial_wait=0.01, max_wait=0.02)
    def always_fail():
        attempts["n"] += 1
        raise ApiException(status=500, reason="server error")

    with pytest.raises(ApiException):
        always_fail()
    assert attempts["n"] == 3


def test_with_retry_non_retryable_raises_immediately():
    attempts = {"n": 0}

    @with_retry(max_attempts=3)
    def bad_request():
        attempts["n"] += 1
        raise ApiException(status=400, reason="bad request")

    with pytest.raises(ApiException):
        bad_request()
    # Not retryable -> only one attempt.
    assert attempts["n"] == 1


# ---- create_retry_decorator -------------------------------------------------


def test_create_retry_decorator_success():
    decorator = create_retry_decorator(max_attempts=3)

    @decorator
    def ok():
        return 123

    assert ok() == 123


def test_create_retry_decorator_retries_custom_exception(monkeypatch):
    # Speed up tenacity's wait between attempts.
    monkeypatch.setattr("time.sleep", lambda _s: None)
    attempts = {"n": 0}

    decorator = create_retry_decorator(
        max_attempts=3,
        initial_wait=0.01,
        max_wait=0.02,
        retry_on=(ValueError,),
    )

    @decorator
    def flaky():
        attempts["n"] += 1
        if attempts["n"] < 2:
            raise ValueError("transient")
        return "ok"

    assert flaky() == "ok"
    assert attempts["n"] == 2
