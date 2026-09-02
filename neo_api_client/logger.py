"""
Structured logging configuration for Neo API Client.

This module provides enterprise-grade logging with structured output,
correlation IDs, and configurable log levels.
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import structlog
from structlog.types import FilteringBoundLogger

# All SDK log timestamps are IST (Asia/Kolkata), regardless of the host
# process's own timezone -- structlog's built-in TimeStamper defaults to UTC,
# which QA flagged as confusing next to IST-based trade timestamps elsewhere
# on the platform.
_IST = ZoneInfo("Asia/Kolkata")


def add_ist_timestamp(
    logger: logging.Logger, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Stamp the event with the current time in IST."""
    event_dict["timestamp"] = datetime.now(_IST).isoformat()
    return event_dict


# Configure log level from environment. Defaults to WARNING so the SDK is
# quiet out of the box -- request/response tracing (api_request_start/
# success) logs at INFO, lifecycle noise (rest_client_initialized/closing)
# at DEBUG; only warnings and errors are visible unless a caller explicitly
# opts into more verbosity via NEO_LOG_LEVEL=INFO or DEBUG.
LOG_LEVEL = os.getenv("NEO_LOG_LEVEL", "WARNING").upper()

# Rotating file log -- on by default, independent of the console level above.
# One file per calendar day (rotated at midnight), always JSON regardless of
# the console's format, since it's meant for later analysis, not a terminal.
FILE_LOG_ENABLED = os.getenv("NEO_LOG_FILE_ENABLED", "true").lower() == "true"
FILE_LOG_PATH = os.getenv("NEO_LOG_FILE_PATH", os.path.join("logs", "neo-api-client.log"))
FILE_LOG_LEVEL = os.getenv("NEO_LOG_FILE_LEVEL", "WARNING").upper()
FILE_LOG_BACKUP_COUNT = int(os.getenv("NEO_LOG_FILE_BACKUP_COUNT", "7"))

# Sentinel accepted by `level`/`file_level` to disable that output entirely
# (e.g. setup_logging(file_level="NOLOG") stops writing to the log file).
NOLOG = "NOLOG"


def _level_value(name: str) -> int | None:
    """Resolve a level name to its numeric logging value, or None for the
    NOLOG sentinel (meaning: disable this handler entirely)."""
    if name.upper() == NOLOG:
        return None
    return getattr(logging, name.upper())


# Handlers setup_logging() itself has attached to the root logger. Tracked so
# each call can remove exactly its own previous handlers before adding new
# ones -- otherwise repeated calls (e.g. a caller reconfiguring the level at
# runtime) would keep piling up handlers instead of replacing them, causing
# duplicate log lines and a later setup_logging(level="NOLOG") failing to
# actually silence anything an earlier call had already attached.
_managed_handlers: list[logging.Handler] = []


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
    # set_environment() (called from RESTClientObject.__init__ with the
    # active client's configuration.host) binds the real "prod"/"uat" value
    # via contextvars, which merge_contextvars already placed in event_dict
    # by the time this runs -- setdefault so it isn't clobbered. Falls back
    # to NEO_ENVIRONMENT / "unknown" only when nothing has bound one yet
    # (e.g. no NeoAPI/RESTClientObject has been constructed in this context).
    event_dict.setdefault("environment", os.getenv("NEO_ENVIRONMENT", "unknown"))
    return event_dict


def set_environment(environment: str) -> None:
    """Bind the active trading environment (e.g. "prod"/"uat") so every
    subsequent log entry in this context carries it, instead of "unknown"."""
    structlog.contextvars.bind_contextvars(environment=environment)


def censor_sensitive_data(
    logger: logging.Logger, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Censor sensitive information from logs."""
    # Deliberately explicit, credential-shaped field names rather than a
    # bare "token" substring -- a bare "token" catches non-sensitive fields
    # too (e.g. quotes()'s exchange_token, WsToken's instrument_token), which
    # are instrument identifiers, not credentials, and shouldn't be masked.
    sensitive_keys = {
        "password",
        "secret",
        "auth",
        "api_key",
        "consumer_key",
        "consumer_secret",
        "bearer_token",
        "edit_token",
        "view_token",
        "access_token",
        "sid",
        "otp",
        "mpin",
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
    level: str = LOG_LEVEL,
    json_output: bool = True,
    show_caller: bool = False,
    file_enabled: bool = FILE_LOG_ENABLED,
    file_path: str = FILE_LOG_PATH,
    file_level: str = FILE_LOG_LEVEL,
    file_backup_count: int = FILE_LOG_BACKUP_COUNT,
) -> FilteringBoundLogger:
    """
    Configure structured logging for the SDK.

    Two independent outputs, each with its own level:

    - **Console** (stdout): controlled by ``level``/``json_output``.
    - **Rotating file**: controlled by ``file_enabled``/``file_path``/
      ``file_level``. On by default. Rotates at midnight (one file per
      calendar day), keeps ``file_backup_count`` days, and is always JSON
      regardless of ``json_output`` -- it's meant for later analysis, not a
      terminal. A failure to create the file (e.g. read-only filesystem, no
      permissions) is swallowed and falls back to console-only logging; it
      must never break the SDK.

    Args:
        level: Console log level (DEBUG, INFO, WARNING, ERROR, CRITICAL, or
            NOLOG to disable console output entirely)
        json_output: If True, console output is JSON; if False, colored console format
        show_caller: If True, include caller information
        file_enabled: Whether to also log to a rotating file
        file_path: Path to the log file (parent directory created if missing)
        file_level: Log level for the file handler, independent of ``level``
            (DEBUG, INFO, WARNING, ERROR, CRITICAL, or NOLOG to disable the
            file entirely -- equivalent to file_enabled=False)
        file_backup_count: How many rotated daily files to keep

    Returns:
        Configured logger instance
    """
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        add_correlation_id,
        add_app_context,
        add_ist_timestamp,
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
    # Defer final rendering to each stdlib handler's own formatter (below),
    # so the console and file outputs can use different renderers (colored
    # console text vs. always-JSON) from this one shared processor pipeline.
    shared_processors.append(structlog.stdlib.ProcessorFormatter.wrap_for_formatter)

    structlog.configure(
        processors=shared_processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Third-party libraries (httpx, httpcore, ...) log through plain stdlib
    # `logging`, not structlog, and propagate up to the root logger same as
    # our own events. Without this, ProcessorFormatter renders those "foreign"
    # records straight from their raw message -- skipping the whole
    # shared_processors chain above -- so they show up with no timestamp, no
    # level, and no censoring. foreign_pre_chain runs just for those records,
    # before the same final render step our own events get.
    foreign_pre_chain = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        add_app_context,
        add_ist_timestamp,
        censor_sensitive_data,
    ]

    root_logger = logging.getLogger()

    # Remove exactly the handlers a previous setup_logging() call attached
    # (never a handler added by something else, e.g. pytest's own log
    # capture), so this call fully replaces the prior configuration instead
    # of accumulating on top of it.
    for old_handler in _managed_handlers:
        root_logger.removeHandler(old_handler)
        old_handler.close()
    _managed_handlers.clear()

    handler_levels = []

    console_level = _level_value(level)
    if console_level is not None:
        console_renderer = (
            structlog.processors.JSONRenderer()
            if json_output
            else structlog.dev.ConsoleRenderer(colors=True)
        )
        console_formatter = structlog.stdlib.ProcessorFormatter(
            foreign_pre_chain=foreign_pre_chain,
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                console_renderer,
            ],
        )
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(console_level)
        root_logger.addHandler(console_handler)
        _managed_handlers.append(console_handler)
        handler_levels.append(console_level)

    file_level_value = _level_value(file_level) if file_enabled else None
    if file_level_value is not None:
        try:
            parent_dir = os.path.dirname(file_path)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)

            file_formatter = structlog.stdlib.ProcessorFormatter(
                foreign_pre_chain=foreign_pre_chain,
                processors=[
                    structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                    structlog.processors.JSONRenderer(),
                ],
            )
            file_handler = logging.handlers.TimedRotatingFileHandler(
                file_path,
                when="midnight",
                backupCount=file_backup_count,
                encoding="utf-8",
            )
            file_handler.setFormatter(file_formatter)
            file_handler.setLevel(file_level_value)
            root_logger.addHandler(file_handler)
            _managed_handlers.append(file_handler)
            handler_levels.append(file_level_value)
        except OSError:
            pass  # Logging setup must never break the SDK; console still works.

    # Root level must be permissive enough for the noisiest handler, or its
    # records never reach any handler regardless of that handler's own level.
    # If every output is NOLOG, set it above CRITICAL so nothing is processed.
    root_logger.setLevel(min(handler_levels) if handler_levels else logging.CRITICAL + 1)

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
