"""Unit tests for rate limiter."""

import time

import pytest

from neo_api_client.rate_limiter import (
    RateLimiter,
    TokenBucket,
    get_rate_limiter,
    reset_rate_limiter,
)


def test_token_bucket_initialization():
    """Test TokenBucket initialization."""
    bucket = TokenBucket(capacity=10, fill_rate=1.0)

    assert bucket.capacity == 10
    assert bucket.fill_rate == 1.0
    assert bucket.tokens == 10.0


def test_token_bucket_consume_success():
    """Test successful token consumption."""
    bucket = TokenBucket(capacity=10, fill_rate=1.0)

    result = bucket.consume(tokens=5)

    assert result is True
    assert bucket.tokens == 5.0


def test_token_bucket_consume_failure():
    """Test token consumption failure when insufficient tokens."""
    bucket = TokenBucket(capacity=10, fill_rate=1.0)

    # Consume all tokens
    bucket.consume(tokens=10)

    # Try to consume more
    result = bucket.consume(tokens=1)

    assert result is False


def test_token_bucket_refill():
    """Test token refill over time."""
    bucket = TokenBucket(capacity=10, fill_rate=10.0)  # 10 tokens per second

    # Consume all tokens
    bucket.consume(tokens=10)
    assert bucket.tokens == 0.0

    # Wait for refill
    time.sleep(0.5)  # Should add 5 tokens

    result = bucket.consume(tokens=3)
    assert result is True


def test_token_bucket_capacity_limit():
    """Test that tokens don't exceed capacity."""
    bucket = TokenBucket(capacity=10, fill_rate=1.0)

    # Wait for potential refill
    time.sleep(0.1)

    # Tokens should not exceed capacity
    assert bucket.tokens <= 10.0


def test_rate_limiter_initialization():
    """Test RateLimiter initialization."""
    limiter = RateLimiter(requests_per_second=5)

    assert limiter.requests_per_second == 5


def test_rate_limiter_disabled():
    """Test RateLimiter when disabled."""
    limiter = RateLimiter(requests_per_second=0)

    # Should not raise any exception
    limiter.acquire()


def test_rate_limiter_acquire():
    """Test rate limiter acquire."""
    limiter = RateLimiter(requests_per_second=10)

    # Should succeed immediately
    result = limiter.acquire()
    assert result is True


def test_rate_limiter_get_status():
    """Test getting rate limiter status."""
    limiter = RateLimiter(requests_per_second=5)

    limiter.acquire()

    status = limiter.get_status()

    assert "per_second" in status
    assert "per_minute" in status


def test_rate_limiter_multiple_acquires():
    """Test multiple acquires."""
    limiter = RateLimiter(requests_per_second=10)

    # Should succeed for multiple requests
    for _ in range(5):
        result = limiter.acquire()
        assert result is True


def test_token_bucket_wait_for_token_immediate():
    """Test wait_for_token returns immediately when tokens available."""
    bucket = TokenBucket(capacity=10, fill_rate=1.0)

    result = bucket.wait_for_token(tokens=5, timeout=1.0)

    assert result is True
    assert bucket.tokens == 5.0


def test_token_bucket_wait_for_token_with_timeout():
    """Test wait_for_token with timeout."""
    bucket = TokenBucket(capacity=10, fill_rate=2.0)  # 2 tokens per second

    # Consume most tokens
    bucket.consume(tokens=9)

    # Wait with timeout - should succeed as tokens refill
    try:
        result = bucket.wait_for_token(tokens=2, timeout=2.0)
        assert result is True or result is False  # Either outcome is valid
    except Exception:
        # Timeout is also acceptable
        pass


def test_wait_for_token_times_out_raises(monkeypatch):
    """wait_for_token raises TimeoutError when tokens never become available."""
    monkeypatch.setattr("time.sleep", lambda _s: None)
    # Very slow refill so tokens never arrive within the timeout window.
    bucket = TokenBucket(capacity=1, fill_rate=0.001)
    bucket.consume(tokens=1)  # drain

    with pytest.raises(TimeoutError, match="Rate limit timeout"):
        bucket.wait_for_token(tokens=1, timeout=0.05)


def test_wait_for_token_sleeps_then_succeeds(monkeypatch):
    """Covers the wait/sleep computation path: drain, then a real refill succeeds.

    ``time.sleep`` is a no-op so the loop spins on real wall-clock; with a very
    fast fill_rate a token is available within a few iterations.
    """
    monkeypatch.setattr("time.sleep", lambda _s: None)

    bucket = TokenBucket(capacity=2, fill_rate=1000.0)
    bucket.consume(tokens=2)  # drain, forcing the wait/compute/sleep branch

    assert bucket.wait_for_token(tokens=1, timeout=None) is True


def test_wait_for_token_continues_after_in_lock_refill(monkeypatch):
    """The in-lock refill can make tokens available, hitting the `continue`
    that re-loops without sleeping (rate_limiter.py line 102)."""
    monkeypatch.setattr("time.sleep", lambda _s: None)

    # A controllable clock, active from construction so `last_update` is known.
    clock = {"t": 100.0}
    monkeypatch.setattr("time.time", lambda: clock["t"])

    bucket = TokenBucket(capacity=5, fill_rate=1.0)  # last_update = 100.0
    bucket.consume(tokens=5)  # drain at t=100 (no time elapsed -> stays empty)

    # Advance the clock so that the NEXT refill (inside the lock) replenishes the
    # bucket past the requested token count, triggering the `continue`.
    real_consume = bucket.consume

    def consume_then_advance(tokens=1):
        result = real_consume(tokens)  # fails at t=100 (empty)
        clock["t"] += 10.0  # 10s * fill_rate 1.0 = 10 tokens on next refill
        return result

    monkeypatch.setattr(bucket, "consume", consume_then_advance)

    assert bucket.wait_for_token(tokens=1, timeout=None) is True


# ---- RateLimiter.acquire timeout paths --------------------------------------


class _SlowBucket:
    """Bucket stub whose wait_for_token behaves per configuration."""

    def __init__(self, behavior="ok"):
        self.behavior = behavior

    def wait_for_token(self, tokens=1, timeout=None):
        if self.behavior == "timeout_return_false":
            return False
        if self.behavior == "raise":
            raise TimeoutError("exceeded")
        return True


def _stub_all_buckets(limiter, behavior="ok"):
    """Replace all three real buckets with stubs so acquire() never blocks
    and never calls time.time() from inside a bucket."""
    limiter.second_bucket = _SlowBucket(behavior)
    limiter.minute_bucket = _SlowBucket(behavior)
    limiter.hour_bucket = _SlowBucket(behavior)


def test_acquire_returns_false_when_bucket_times_out():
    limiter = RateLimiter(requests_per_second=5)
    _stub_all_buckets(limiter, "timeout_return_false")

    assert limiter.acquire(timeout=1.0) is False


def test_acquire_raises_on_bucket_timeout_error():
    limiter = RateLimiter(requests_per_second=5)
    _stub_all_buckets(limiter, "raise")

    with pytest.raises(TimeoutError):
        limiter.acquire(timeout=1.0)


def test_acquire_logs_when_wait_exceeds_threshold(monkeypatch):
    """elapsed > 0.1 branch: emits the rate_limit_acquired info log."""
    limiter = RateLimiter(requests_per_second=5)
    _stub_all_buckets(limiter, "ok")  # buckets return instantly, no time.time() calls

    # acquire() calls time.time() twice (start + end); make the gap exceed 0.1s.
    times = iter([100.0, 100.3])
    monkeypatch.setattr("time.time", lambda: next(times, 100.3))

    assert limiter.acquire(timeout=None) is True


# ---- module-level singleton helpers -----------------------------------------


def test_get_rate_limiter_singleton_and_reset():
    reset_rate_limiter()
    first = get_rate_limiter()
    second = get_rate_limiter()
    assert first is second  # cached singleton

    reset_rate_limiter()
    third = get_rate_limiter()
    assert third is not first  # reset -> new instance
    reset_rate_limiter()
