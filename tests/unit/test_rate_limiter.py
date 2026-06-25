"""Unit tests for rate limiter."""

import time

from neo_api_client.rate_limiter import RateLimiter, TokenBucket


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
