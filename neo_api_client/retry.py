"""
Retry logic with exponential backoff for API requests.

Implements enterprise-grade retry mechanisms with jitter,
configurable backoff, and selective retry for transient errors.
"""

import logging
import random
from collections.abc import Callable
from functools import wraps

from tenacity import (
    after_log,
    before_sleep_log,
    retry,
    retry_if_exception,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from neo_api_client.exceptions import ApiException
from neo_api_client.logger import get_logger

logger = get_logger(__name__)


class RetryConfig:
    """Configuration for retry behavior."""

    # Maximum number of retry attempts
    MAX_ATTEMPTS = 3

    # Initial wait time in seconds
    INITIAL_WAIT = 1

    # Maximum wait time in seconds
    MAX_WAIT = 30

    # Multiplier for exponential backoff
    MULTIPLIER = 2

    # Jitter range (min, max) in seconds
    JITTER_RANGE = (0, 2)

    # HTTP status codes that should be retried
    RETRYABLE_STATUS_CODES = {
        408,  # Request Timeout
        429,  # Too Many Requests
        500,  # Internal Server Error
        502,  # Bad Gateway
        503,  # Service Unavailable
        504,  # Gateway Timeout
    }


def should_retry_exception(exception: Exception) -> bool:
    """
    Determine if an exception should trigger a retry.

    Args:
        exception: The exception that was raised

    Returns:
        True if the exception should be retried, False otherwise
    """
    # Retry on specific ApiException status codes
    if isinstance(exception, ApiException):
        if hasattr(exception, "status") and exception.status:
            return exception.status in RetryConfig.RETRYABLE_STATUS_CODES
        # Retry on connection errors
        if hasattr(exception, "category"):
            from neo_api_client.exceptions import ErrorCategory

            return exception.category in {
                ErrorCategory.NETWORK,
                ErrorCategory.TIMEOUT,
                ErrorCategory.RATE_LIMIT,
            }

    # Retry on network-related exceptions
    try:
        import httpx

        # TimeoutException + ConnectError both derive from httpx.HTTPError, so the
        # base class covers transport/timeout/HTTP failures in one check.
        return isinstance(exception, httpx.HTTPError)
    except ImportError:
        pass

    return False


def add_jitter(wait_time: float) -> float:
    """
    Add random jitter to wait time to prevent thundering herd.

    Args:
        wait_time: Base wait time in seconds

    Returns:
        Wait time with jitter added
    """
    jitter = random.uniform(*RetryConfig.JITTER_RANGE)
    return wait_time + jitter


def create_retry_decorator(
    max_attempts: int = RetryConfig.MAX_ATTEMPTS,
    initial_wait: float = RetryConfig.INITIAL_WAIT,
    max_wait: float = RetryConfig.MAX_WAIT,
    multiplier: float = RetryConfig.MULTIPLIER,
    retry_on: tuple[type[Exception], ...] | None = None,
) -> Callable:
    """
    Create a retry decorator with exponential backoff.

    Args:
        max_attempts: Maximum number of attempts (including initial)
        initial_wait: Initial wait time in seconds
        max_wait: Maximum wait time in seconds
        multiplier: Multiplier for exponential backoff
        retry_on: Tuple of exception types to retry on

    Returns:
        Retry decorator function

    Example:
        >>> @create_retry_decorator(max_attempts=3)
        ... def my_function():
        ...     # May fail transiently
        ...     return api_call()
    """

    def should_retry(exc: Exception) -> bool:
        """Check if exception should be retried."""
        if retry_on and isinstance(exc, retry_on):
            return True
        return should_retry_exception(exc)

    return retry(
        retry=retry_if_exception_type(Exception) & retry_if_exception(should_retry),
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(
            multiplier=multiplier,
            min=initial_wait,
            max=max_wait,
        ),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        after=after_log(logger, logging.DEBUG),
        reraise=True,
    )


def with_retry(
    max_attempts: int = RetryConfig.MAX_ATTEMPTS,
    initial_wait: float = RetryConfig.INITIAL_WAIT,
    max_wait: float = RetryConfig.MAX_WAIT,
) -> Callable:
    """
    Decorator to add retry logic to a function.

    Args:
        max_attempts: Maximum number of attempts
        initial_wait: Initial wait time in seconds
        max_wait: Maximum wait time in seconds

    Returns:
        Decorated function with retry logic

    Example:
        >>> @with_retry(max_attempts=3)
        ... def fetch_data():
        ...     return requests.get(url)
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            last_exception = None

            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    attempt += 1

                    if attempt >= max_attempts:
                        logger.error(
                            "max_retries_exceeded",
                            function=func.__name__,
                            attempts=attempt,
                            error=str(e),
                        )
                        raise

                    if should_retry_exception(e):
                        wait_time = min(
                            initial_wait * (RetryConfig.MULTIPLIER ** (attempt - 1)), max_wait
                        )
                        wait_time = add_jitter(wait_time)

                        logger.warning(
                            "retrying_request",
                            function=func.__name__,
                            attempt=attempt,
                            max_attempts=max_attempts,
                            wait_seconds=round(wait_time, 2),
                            error=str(e),
                        )

                        import time

                        time.sleep(wait_time)
                    else:
                        # Not a retryable exception
                        logger.error(
                            "non_retryable_exception",
                            function=func.__name__,
                            error=str(e),
                            error_type=type(e).__name__,
                        )
                        raise

            # Should never reach here, but just in case
            if last_exception:  # pragma: no cover - loop always returns or raises
                raise last_exception

        return wrapper

    return decorator
