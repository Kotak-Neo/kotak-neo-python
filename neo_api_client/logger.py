"""
Structured logging configuration for Neo API Client.

This module provides enterprise-grade logging with structured output,
correlation IDs, and configurable log levels.
"""

import logging
import os
import sys
from typing import Any

import structlog
from structlog.types import FilteringBoundLogger

# Configure log level from environment. Defaults to WARNING so the SDK is
# quiet out of the box -- routine per-request tracing (api_request_start/
# success, rest_client_initialized/closing) logs at DEBUG; only warnings and
# errors are visible unless a caller explicitly opts into more verbosity via
# NEO_LOG_LEVEL=INFO or DEBUG.
LOG_LEVEL = os.getenv("NEO_LOG_LEVEL", "WARNING").upper()


def add_correlation_id(
    logger: logging.Logger, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Add correlation ID from context if available."""
    from contextvars import ContextVar

    correlation_id: ContextVar[str | None] = ContextVar("correlation_id", default=None)
    cid = correlation_id.get()
    if cid:
        event_dict["correlation_id"] = cid
    return event_dict


def add_app_context(
    logger: logging.Logger, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Add application context to logs."""
    event_dict["app"] = "neo_api_client"
    event_dict["environment"] = os.getenv("NEO_ENVIRONMENT", "unknown")
    return event_dict


def censor_sensitive_data(
    logger: logging.Logger, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Censor sensitive information from logs."""
    sensitive_keys = {
        "password",
        "secret",
        "token",
        "authorization",
        "api_key",
        "consumer_key",
        "consumer_secret",
        "bearer_token",
        "edit_token",
        "view_token",
        "sid",
        "otp",
    }

    def _censor_dict(d: dict[str, Any]) -> dict[str, Any]:
        """Recursively censor sensitive data."""
        censored = {}
        for key, value in d.items():
            lower_key = key.lower()
            if any(sensitive in lower_key for sensitive in sensitive_keys):
                # Show only first and last 2 chars for debugging
                if isinstance(value, str) and len(value) > 4:
                    censored[key] = f"{value[:2]}***{value[-2:]}"
                else:
                    censored[key] = "***"
            elif isinstance(value, dict):
                censored[key] = _censor_dict(value)
            elif isinstance(value, list):
                censored[key] = [
                    _censor_dict(item) if isinstance(item, dict) else item for item in value
                ]
            else:
                censored[key] = value
        return censored

    return _censor_dict(event_dict)


def setup_logging(
    level: str = LOG_LEVEL, json_output: bool = True, show_caller: bool = False
) -> FilteringBoundLogger:
    """
    Configure structured logging for the SDK.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_output: If True, output JSON; if False, use console format
        show_caller: If True, include caller information

    Returns:
        Configured logger instance
    """
    timestamper = structlog.processors.TimeStamper(fmt="iso")

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        add_correlation_id,
        add_app_context,
        timestamper,
    ]

    if show_caller:
        # Pin an explicit parameter set. structlog >= 25 adds QUAL_NAME /
        # QUAL_MODULE to the default set, which read frame.f_code.co_qualname —
        # an attribute that only exists on Python 3.11+. Since the SDK supports
        # 3.10, we select 3.10-safe parameters explicitly.
        CP = structlog.processors.CallsiteParameter
        shared_processors.append(
            structlog.processors.CallsiteParameterAdder(
                parameters={
                    CP.MODULE,
                    CP.FUNC_NAME,
                    CP.LINENO,
                    CP.FILENAME,
                    CP.PATHNAME,
                    CP.THREAD,
                    CP.THREAD_NAME,
                    CP.PROCESS,
                    CP.PROCESS_NAME,
                }
            )
        )

    # Always censor sensitive data
    shared_processors.append(censor_sensitive_data)

    if json_output:
        # JSON output for production
        structlog.configure(
            processors=shared_processors
            + [
                structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
            ],
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )

        formatter = structlog.stdlib.ProcessorFormatter(
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                structlog.processors.JSONRenderer(),
            ],
        )
    else:
        # Console output for development
        structlog.configure(
            processors=shared_processors
            + [
                structlog.dev.ConsoleRenderer(colors=True),
            ],
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )
        formatter = None

    # Configure standard library logging
    handler = logging.StreamHandler(sys.stdout)
    if formatter:
        handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, level))

    # Return a bound logger
    return structlog.get_logger()


# Create default logger instance
logger = setup_logging(
    level=LOG_LEVEL,
    json_output=os.getenv("NEO_LOG_JSON", "true").lower() == "true",
    show_caller=os.getenv("NEO_LOG_SHOW_CALLER", "false").lower() == "true",
)


def get_logger(name: str | None = None) -> FilteringBoundLogger:
    """
    Get a logger instance.

    Args:
        name: Optional logger name (usually __name__)

    Returns:
        Configured logger instance
    """
    if name:
        return structlog.get_logger(name)
    return logger
