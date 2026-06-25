"""
Rate limiting implementation for API requests.

Implements token bucket algorithm to prevent API quota exhaustion
and account suspension due to excessive requests.
"""

import os
import threading
import time

from neo_api_client.logger import get_logger

logger = get_logger(__name__)


class TokenBucket:
    """
    Token bucket algorithm implementation for rate limiting.

    Attributes:
        capacity: Maximum number of tokens in bucket
        fill_rate: Rate at which tokens are added (tokens per second)
        tokens: Current number of available tokens
        last_update: Timestamp of last token update
    """

    def __init__(self, capacity: int, fill_rate: float):
        """
        Initialize token bucket.

        Args:
            capacity: Maximum tokens (burst capacity)
            fill_rate: Tokens added per second
        """
        self.capacity = capacity
        self.fill_rate = fill_rate
        self.tokens = float(capacity)
        self.last_update = time.time()
        self._lock = threading.Lock()

    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_update

        # Add tokens based on elapsed time
        new_tokens = elapsed * self.fill_rate
        self.tokens = min(self.capacity, self.tokens + new_tokens)
        self.last_update = now

    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens from bucket.

        Args:
            tokens: Number of tokens to consume

        Returns:
            True if tokens were consumed, False otherwise
        """
        with self._lock:
            self._refill()

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    def wait_for_token(self, tokens: int = 1, timeout: float | None = None) -> bool:
        """
        Wait until tokens are available.

        Args:
            tokens: Number of tokens needed
            timeout: Maximum wait time in seconds (None = infinite)

        Returns:
            True if tokens acquired, False if timeout

        Raises:
            TimeoutError: If timeout is reached
        """
        start_time = time.time()

        while True:
            if self.consume(tokens):
                return True

            # Check timeout
            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    raise TimeoutError(
                        f"Rate limit timeout after {elapsed:.2f}s waiting for {tokens} tokens"
                    )

            # Calculate wait time
            with self._lock:
                self._refill()
                if self.tokens >= tokens:
                    continue

                tokens_needed = tokens - self.tokens
                wait_time = tokens_needed / self.fill_rate
                wait_time = min(wait_time, 1.0)  # Max 1 second wait per iteration

            logger.debug(
                "rate_limit_wait",
                tokens_needed=tokens_needed,
                wait_seconds=round(wait_time, 3),
            )

            time.sleep(wait_time)

    def get_available_tokens(self) -> float:
        """
        Get current number of available tokens.

        Returns:
            Number of available tokens
        """
        with self._lock:
            self._refill()
            return self.tokens


class RateLimiter:
    """
    Multi-tier rate limiter for API requests.

    Implements rate limiting at multiple time scales:
    - Per second (burst protection)
    - Per minute (sustained load)
    - Per hour (quota management)
    """

    def __init__(
        self,
        requests_per_second: int | None = None,
        requests_per_minute: int | None = None,
        requests_per_hour: int | None = None,
    ):
        """
        Initialize rate limiter with configurable limits.

        Args:
            requests_per_second: Max requests per second (None = unlimited)
            requests_per_minute: Max requests per minute (None = unlimited)
            requests_per_hour: Max requests per hour (None = unlimited)
        """
        # Load from environment with fallbacks
        self.requests_per_second = requests_per_second or int(
            os.getenv("NEO_MAX_REQUESTS_PER_SECOND", "10")
        )
        self.requests_per_minute = requests_per_minute or int(
            os.getenv("NEO_MAX_REQUESTS_PER_MINUTE", "300")
        )
        self.requests_per_hour = requests_per_hour or int(
            os.getenv("NEO_MAX_REQUESTS_PER_HOUR", "5000")
        )

        # Create token buckets
        self.second_bucket = TokenBucket(
            capacity=self.requests_per_second,
            fill_rate=self.requests_per_second,
        )

        self.minute_bucket = TokenBucket(
            capacity=self.requests_per_minute,
            fill_rate=self.requests_per_minute / 60.0,
        )

        self.hour_bucket = TokenBucket(
            capacity=self.requests_per_hour,
            fill_rate=self.requests_per_hour / 3600.0,
        )

        logger.info(
            "rate_limiter_initialized",
            per_second=self.requests_per_second,
            per_minute=self.requests_per_minute,
            per_hour=self.requests_per_hour,
        )

    def acquire(self, timeout: float | None = 30.0) -> bool:
        """
        Acquire permission to make a request.

        Args:
            timeout: Maximum time to wait for permission (seconds)

        Returns:
            True if permission granted

        Raises:
            TimeoutError: If timeout is reached
        """
        start_time = time.time()

        # Try to acquire from all buckets
        buckets = [
            ("second", self.second_bucket),
            ("minute", self.minute_bucket),
            ("hour", self.hour_bucket),
        ]

        for name, bucket in buckets:
            remaining_timeout = (
                None if timeout is None else max(0, timeout - (time.time() - start_time))
            )

            try:
                if not bucket.wait_for_token(tokens=1, timeout=remaining_timeout):
                    logger.warning(
                        "rate_limit_timeout",
                        bucket=name,
                        timeout=timeout,
                    )
                    return False
            except TimeoutError:
                logger.error(
                    "rate_limit_exceeded",
                    bucket=name,
                    timeout=timeout,
                    elapsed=time.time() - start_time,
                )
                raise

        elapsed = time.time() - start_time
        if elapsed > 0.1:  # Log if we had to wait
            logger.info(
                "rate_limit_acquired",
                wait_seconds=round(elapsed, 3),
            )

        return True

    def get_status(self) -> dict:
        """
        Get current rate limiter status.

        Returns:
            Dictionary with current token counts
        """
        return {
            "per_second": {
                "capacity": self.requests_per_second,
                "available": round(self.second_bucket.get_available_tokens(), 2),
            },
            "per_minute": {
                "capacity": self.requests_per_minute,
                "available": round(self.minute_bucket.get_available_tokens(), 2),
            },
            "per_hour": {
                "capacity": self.requests_per_hour,
                "available": round(self.hour_bucket.get_available_tokens(), 2),
            },
        }


# Global rate limiter instance (can be overridden per client)
_default_rate_limiter: RateLimiter | None = None


def get_rate_limiter() -> RateLimiter:
    """
    Get or create the default rate limiter instance.

    Returns:
        Global rate limiter instance
    """
    global _default_rate_limiter
    if _default_rate_limiter is None:
        _default_rate_limiter = RateLimiter()
    return _default_rate_limiter


def reset_rate_limiter() -> None:
    """Reset the global rate limiter (useful for testing)."""
    global _default_rate_limiter
    _default_rate_limiter = None
