"""
Circuit breaker pattern implementation.

Prevents cascading failures by stopping requests to failing services
and allowing them time to recover.
"""

import threading
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from neo_api_client.logger import get_logger

logger = get_logger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Blocking requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""

    failure_threshold: int = 5  # Failures before opening
    success_threshold: int = 2  # Successes in half-open to close
    timeout: float = 60.0  # Seconds before trying again
    expected_exception: type = Exception  # Exception type to catch


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open."""

    def __init__(self, message: str, circuit_name: str, retry_after: float):
        super().__init__(message)
        self.circuit_name = circuit_name
        self.retry_after = retry_after


class CircuitBreaker:
    """
    Circuit breaker implementation.

    Monitors failures and prevents requests when threshold is exceeded.
    Automatically attempts recovery after timeout period.
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout: float = 60.0,
        expected_exception: type = Exception,
    ):
        """
        Initialize circuit breaker.

        Args:
            name: Identifier for this circuit
            failure_threshold: Number of failures before opening
            success_threshold: Successes needed to close from half-open
            timeout: Seconds before attempting recovery
            expected_exception: Exception type to monitor
        """
        self.name = name
        self.config = CircuitBreakerConfig(
            failure_threshold=failure_threshold,
            success_threshold=success_threshold,
            timeout=timeout,
            expected_exception=expected_exception,
        )

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: datetime | None = None
        self._lock = threading.Lock()

        logger.info(
            "circuit_breaker_initialized",
            name=name,
            failure_threshold=failure_threshold,
            timeout=timeout,
        )

    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        return self._state

    @property
    def failure_count(self) -> int:
        """Get current failure count."""
        return self._failure_count

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self._last_failure_time is None:
            return False

        elapsed = (datetime.now(timezone.utc) - self._last_failure_time).total_seconds()
        return elapsed >= self.config.timeout

    def _record_success(self) -> None:
        """Record successful call."""
        with self._lock:
            self._failure_count = 0

            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1

                if self._success_count >= self.config.success_threshold:
                    self._state = CircuitState.CLOSED
                    self._success_count = 0
                    logger.info(
                        "circuit_breaker_closed",
                        name=self.name,
                        successes=self._success_count,
                    )

    def _record_failure(self) -> None:
        """Record failed call."""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = datetime.now(timezone.utc)

            if self._state == CircuitState.HALF_OPEN:
                # Failed during recovery - reopen immediately
                self._state = CircuitState.OPEN
                self._success_count = 0
                logger.warning(
                    "circuit_breaker_reopened",
                    name=self.name,
                    reason="failure_during_recovery",
                )

            elif self._failure_count >= self.config.failure_threshold:
                # Threshold exceeded - open circuit
                self._state = CircuitState.OPEN
                logger.error(
                    "circuit_breaker_opened",
                    name=self.name,
                    failures=self._failure_count,
                    threshold=self.config.failure_threshold,
                )

    def call(self, func: Callable, *args, **kwargs):
        """
        Execute function with circuit breaker protection.

        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            CircuitBreakerError: If circuit is open
        """
        with self._lock:
            # Check if we should attempt recovery
            if self._state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self._state = CircuitState.HALF_OPEN
                    self._success_count = 0
                    logger.info(
                        "circuit_breaker_half_open",
                        name=self.name,
                    )
                else:
                    # Still open - reject request
                    retry_after = (
                        self.config.timeout
                        - (datetime.now(timezone.utc) - self._last_failure_time).total_seconds()
                    )
                    logger.warning(
                        "circuit_breaker_rejected",
                        name=self.name,
                        state=self._state.value,
                        retry_after=round(retry_after, 2),
                    )
                    raise CircuitBreakerError(
                        f"Circuit breaker '{self.name}' is OPEN",
                        circuit_name=self.name,
                        retry_after=retry_after,
                    )

        # Execute the function
        try:
            result = func(*args, **kwargs)
            self._record_success()
            return result

        except self.config.expected_exception:
            self._record_failure()
            raise

    def __call__(self, func: Callable) -> Callable:
        """
        Decorator for circuit breaker.

        Example:
            >>> breaker = CircuitBreaker("api")
            >>> @breaker
            ... def make_request():
            ...     return api.get()
        """

        def wrapper(*args, **kwargs):
            return self.call(func, *args, **kwargs)

        return wrapper

    def reset(self) -> None:
        """Manually reset the circuit breaker."""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._last_failure_time = None

            logger.info("circuit_breaker_reset", name=self.name)

    def get_status(self) -> dict:
        """
        Get current circuit breaker status.

        Returns:
            Dictionary with status information
        """
        with self._lock:
            status = {
                "name": self.name,
                "state": self._state.value,
                "failure_count": self._failure_count,
                "failure_threshold": self.config.failure_threshold,
            }

            if self._state == CircuitState.HALF_OPEN:
                status["success_count"] = self._success_count
                status["success_threshold"] = self.config.success_threshold

            if self._last_failure_time:
                elapsed = (datetime.now(timezone.utc) - self._last_failure_time).total_seconds()
                status["seconds_since_failure"] = round(elapsed, 2)
                status["retry_after"] = max(0, round(self.config.timeout - elapsed, 2))

            return status


# Global registry of circuit breakers
_circuit_breakers = {}
_registry_lock = threading.Lock()


def get_circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    success_threshold: int = 2,
    timeout: float = 60.0,
) -> CircuitBreaker:
    """
    Get or create a circuit breaker.

    Args:
        name: Circuit breaker name
        failure_threshold: Failures before opening
        success_threshold: Successes to close
        timeout: Timeout before retry

    Returns:
        CircuitBreaker instance
    """
    with _registry_lock:
        if name not in _circuit_breakers:
            _circuit_breakers[name] = CircuitBreaker(
                name=name,
                failure_threshold=failure_threshold,
                success_threshold=success_threshold,
                timeout=timeout,
            )
        return _circuit_breakers[name]


def reset_all_circuit_breakers() -> None:
    """Reset all circuit breakers (useful for testing)."""
    with _registry_lock:
        for breaker in _circuit_breakers.values():
            breaker.reset()


def get_all_circuit_breakers_status() -> dict:
    """
    Get status of all circuit breakers.

    Returns:
        Dictionary mapping names to status
    """
    with _registry_lock:
        return {name: breaker.get_status() for name, breaker in _circuit_breakers.items()}
