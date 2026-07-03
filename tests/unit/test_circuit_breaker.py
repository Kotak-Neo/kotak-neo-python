"""Unit tests for the circuit breaker."""

from datetime import datetime, timedelta, timezone

import pytest

from neo_api_client.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerError,
    CircuitState,
    get_all_circuit_breakers_status,
    get_circuit_breaker,
    reset_all_circuit_breakers,
)


def _boom():
    raise ValueError("boom")


def test_initial_state_closed():
    cb = CircuitBreaker("t1")
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 0


def test_successful_call_passes_through():
    cb = CircuitBreaker("t2")
    assert cb.call(lambda x: x + 1, 41) == 42
    assert cb.state == CircuitState.CLOSED


def test_opens_after_failure_threshold():
    cb = CircuitBreaker("t3", failure_threshold=3)

    for _ in range(3):
        with pytest.raises(ValueError):
            cb.call(_boom)

    assert cb.state == CircuitState.OPEN
    assert cb.failure_count == 3


def test_open_circuit_rejects_calls():
    cb = CircuitBreaker("t4", failure_threshold=1)

    with pytest.raises(ValueError):
        cb.call(_boom)
    assert cb.state == CircuitState.OPEN

    # Now calls are rejected without executing the function.
    with pytest.raises(CircuitBreakerError) as exc_info:
        cb.call(lambda: "should not run")

    assert exc_info.value.circuit_name == "t4"
    assert exc_info.value.retry_after > 0


def test_success_resets_failure_count():
    cb = CircuitBreaker("t5", failure_threshold=5)

    with pytest.raises(ValueError):
        cb.call(_boom)
    assert cb.failure_count == 1

    cb.call(lambda: "ok")
    assert cb.failure_count == 0


def test_half_open_after_timeout_then_closes():
    cb = CircuitBreaker("t6", failure_threshold=1, success_threshold=2, timeout=60.0)

    with pytest.raises(ValueError):
        cb.call(_boom)
    assert cb.state == CircuitState.OPEN

    # Simulate the timeout elapsing.
    cb._last_failure_time = datetime.now(timezone.utc) - timedelta(seconds=61)

    # Next call transitions to HALF_OPEN and executes; needs success_threshold
    # successes to close.
    assert cb.call(lambda: "ok1") == "ok1"
    assert cb.state == CircuitState.HALF_OPEN

    assert cb.call(lambda: "ok2") == "ok2"
    assert cb.state == CircuitState.CLOSED


def test_half_open_failure_reopens():
    cb = CircuitBreaker("t7", failure_threshold=1, timeout=60.0)

    with pytest.raises(ValueError):
        cb.call(_boom)
    cb._last_failure_time = datetime.now(timezone.utc) - timedelta(seconds=61)

    # A failure during HALF_OPEN recovery reopens immediately.
    with pytest.raises(ValueError):
        cb.call(_boom)
    assert cb.state == CircuitState.OPEN


def test_reset():
    cb = CircuitBreaker("t8", failure_threshold=1)
    with pytest.raises(ValueError):
        cb.call(_boom)
    assert cb.state == CircuitState.OPEN

    cb.reset()
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 0


def test_decorator_usage():
    cb = CircuitBreaker("t9", failure_threshold=1)

    @cb
    def add(a, b):
        return a + b

    assert add(2, 3) == 5


def test_get_status_closed():
    cb = CircuitBreaker("t10", failure_threshold=4)
    status = cb.get_status()
    assert status["name"] == "t10"
    assert status["state"] == "closed"
    assert status["failure_count"] == 0
    assert status["failure_threshold"] == 4


def test_get_status_after_failure_has_retry_fields():
    cb = CircuitBreaker("t11", failure_threshold=1, timeout=60.0)
    with pytest.raises(ValueError):
        cb.call(_boom)

    status = cb.get_status()
    assert status["state"] == "open"
    assert "seconds_since_failure" in status
    assert "retry_after" in status


def test_expected_exception_filter_ignores_other_errors():
    cb = CircuitBreaker("t12", failure_threshold=2, expected_exception=ValueError)

    # A non-ValueError is not counted as a monitored failure.
    with pytest.raises(KeyError):
        cb.call(lambda: (_ for _ in ()).throw(KeyError("x")))
    assert cb.failure_count == 0
    assert cb.state == CircuitState.CLOSED


def test_registry_get_and_reuse():
    reset_all_circuit_breakers()
    a = get_circuit_breaker("registry_test", failure_threshold=2)
    b = get_circuit_breaker("registry_test")
    assert a is b  # same instance reused


def test_registry_status_and_reset_all():
    cb = get_circuit_breaker("registry_reset", failure_threshold=1)
    with pytest.raises(ValueError):
        cb.call(_boom)
    assert cb.state == CircuitState.OPEN

    all_status = get_all_circuit_breakers_status()
    assert "registry_reset" in all_status

    reset_all_circuit_breakers()
    assert cb.state == CircuitState.CLOSED
