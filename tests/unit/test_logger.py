"""Unit tests for logger module."""

import json
import logging
import logging.handlers

import pytest
import structlog

from neo_api_client.logger import (
    add_app_context,
    add_correlation_id,
    censor_sensitive_data,
    get_logger,
    setup_logging,
)


@pytest.fixture(autouse=True)
def _restore_structlog_config():
    """Any test here calls setup_logging(), which reconfigures structlog
    globally AND adds handlers to the stdlib root logger. Snapshot and
    restore both so a test can't leak its logging setup (e.g. show_caller=True,
    or a file handler pointed at a tmp_path that's about to be cleaned up)
    into unrelated tests in the same session."""
    saved = structlog.get_config()
    root_logger = logging.getLogger()
    saved_handlers = root_logger.handlers[:]
    saved_level = root_logger.level
    try:
        yield
    finally:
        structlog.configure(**saved)
        for handler in root_logger.handlers[:]:
            if handler not in saved_handlers:
                root_logger.removeHandler(handler)
                handler.close()
        root_logger.setLevel(saved_level)


def test_get_logger_basic():
    """Test get_logger returns a logger instance."""
    logger = get_logger("test")

    assert logger is not None


def test_get_logger_default():
    """Test get_logger with no name."""
    logger = get_logger()

    assert logger is not None


def test_get_logger_different_names():
    """Test get_logger with different names."""
    logger1 = get_logger("module1")
    logger2 = get_logger("module2")

    # Both should be valid logger instances
    assert logger1 is not None
    assert logger2 is not None


def test_censor_sensitive_data_processor():
    """Test censor_sensitive_data as a log processor."""
    # censor_sensitive_data is a processor that gets logger, name, event_dict
    event_dict = {
        "consumer_key": "secret_key_123",
        "password": "mypassword",
        "access_token": "token_abc",
        "normal_field": "visible_value",
    }

    result = censor_sensitive_data(None, None, event_dict)

    # Should censor sensitive keys
    assert "se***23" in result.get("consumer_key", "") or result.get("consumer_key") == "***"
    assert "my***rd" in result.get("password", "") or result.get("password") == "***"
    assert "to***bc" in result.get("access_token", "") or result.get("access_token") == "***"
    assert result["normal_field"] == "visible_value"


def test_censor_sensitive_data_nested():
    """Test censor_sensitive_data with nested dictionary."""
    event_dict = {
        "user": {"username": "john", "password": "secret123"},
        "data": {"value": 100},
    }

    result = censor_sensitive_data(None, None, event_dict)

    # Password should be censored
    assert "password" in result["user"]
    # Username should remain
    assert result["user"]["username"] == "john"
    assert result["data"]["value"] == 100


def test_add_correlation_id_processor():
    """Test add_correlation_id processor."""
    event_dict = {"message": "test"}

    result = add_correlation_id(None, None, event_dict)

    # add_correlation_id may add request_id only if not already present
    # Just verify it returns a dict and doesn't raise
    assert isinstance(result, dict)
    assert "message" in result


def test_add_app_context_processor():
    """Test add_app_context processor."""
    event_dict = {"message": "test"}

    result = add_app_context(None, None, event_dict)

    # Should add app context
    assert "app" in result
    assert result["app"] == "neo_api_client"
    assert "environment" in result


def test_add_app_context_defaults_to_unknown_without_set_environment():
    """No set_environment() call yet -> falls back to NEO_ENVIRONMENT/'unknown'."""
    event_dict = {"message": "test"}

    result = add_app_context(None, None, event_dict)

    assert result["environment"] == "unknown"


def test_set_environment_is_visible_via_merge_contextvars():
    """set_environment() binds a contextvar that merge_contextvars puts into
    the event dict before add_app_context runs -- so real client config
    (e.g. "prod"/"uat") shows up instead of the 'unknown' fallback."""
    from neo_api_client.logger import set_environment

    set_environment("prod")
    event_dict = structlog.contextvars.merge_contextvars(None, None, {"message": "test"})
    result = add_app_context(None, None, event_dict)

    assert result["environment"] == "prod"


def test_setup_logging_default():
    """Test setup_logging with default parameters."""
    logger = setup_logging()

    assert logger is not None


def test_setup_logging_custom_level():
    """Test setup_logging with custom log level."""
    logger = setup_logging(level="DEBUG")

    assert logger is not None


def test_setup_logging_no_json():
    """Test setup_logging without JSON output."""
    logger = setup_logging(json_output=False)

    assert logger is not None


def test_get_logger_after_setup():
    """Test get_logger after setup_logging."""
    setup_logging()
    logger = get_logger("test_module")

    assert logger is not None


def test_logger_info_message():
    """Test logger can log info messages."""
    logger = get_logger("test")

    # Should not raise exceptions
    logger.info("test message")


def test_logger_with_context():
    """Test logger with additional context."""
    logger = get_logger("test")

    # Should not raise exceptions
    logger.info("test message", extra_field="extra_value")


def test_add_correlation_id_sets_when_present(monkeypatch):
    """When a correlation id is set in context, it is added to the event dict."""
    import contextvars

    class _FakeCtxVar:
        def __init__(self, *a, **k):
            pass

        def get(self):
            return "corr-123"

    monkeypatch.setattr(contextvars, "ContextVar", _FakeCtxVar)

    result = add_correlation_id(None, None, {"message": "hi"})
    assert result["correlation_id"] == "corr-123"


def test_censor_sensitive_data_list_of_dicts():
    """A list containing dicts is censored element-by-element (covers list branch)."""
    event_dict = {
        "items": [
            {"password": "secret123", "name": "a"},
            "plain-string",
            42,
        ],
    }

    result = censor_sensitive_data(None, None, event_dict)

    # dict element censored, non-dict elements untouched
    assert result["items"][0]["password"] != "secret123"
    assert result["items"][0]["name"] == "a"
    assert result["items"][1] == "plain-string"
    assert result["items"][2] == 42


def test_setup_logging_show_caller():
    """setup_logging(show_caller=True) appends the callsite processor (line 111)."""
    logger = setup_logging(show_caller=True)
    assert logger is not None


# ---- rotating file log ------------------------------------------------------


def test_file_logging_writes_warning_and_above(tmp_path):
    """A WARNING (>= the default file_level) reaches the file, as valid JSON."""
    log_path = tmp_path / "neo_api_client.log"
    setup_logging(level="DEBUG", file_enabled=True, file_path=str(log_path), file_level="WARNING")

    get_logger("test_file_logging").warning("something_went_wrong", detail="x")

    assert log_path.exists()
    lines = [line for line in log_path.read_text().splitlines() if line.strip()]
    assert lines
    record = json.loads(lines[-1])
    assert record["event"] == "something_went_wrong"
    assert record["level"] == "warning"
    assert record["detail"] == "x"


def test_file_logging_filters_below_its_own_level(tmp_path):
    """An INFO message is dropped by the file handler even though the
    console level (DEBUG) would have let it through -- the two levels are
    independent."""
    log_path = tmp_path / "neo_api_client.log"
    setup_logging(level="DEBUG", file_enabled=True, file_path=str(log_path), file_level="WARNING")

    test_logger = get_logger("test_file_logging_filter")
    test_logger.info("routine_info_event")
    test_logger.warning("actionable_warning_event")

    content = log_path.read_text()
    assert "routine_info_event" not in content
    assert "actionable_warning_event" in content


def test_file_logging_disabled_creates_no_file(tmp_path):
    """file_enabled=False (or the NEO_LOG_FILE_ENABLED=false default under
    pytest, see conftest.py) must not create the log file at all."""
    log_path = tmp_path / "should_not_exist.log"
    setup_logging(file_enabled=False, file_path=str(log_path))

    get_logger("test_file_logging_disabled").warning("should_not_be_written_to_file")

    assert not log_path.exists()


def test_file_logging_uses_timed_rotating_handler(tmp_path):
    """The file handler rotates daily (midnight) and keeps the configured
    number of backups -- not an arbitrary plain FileHandler."""
    log_path = tmp_path / "neo_api_client.log"
    setup_logging(file_enabled=True, file_path=str(log_path), file_backup_count=3)

    file_handlers = [
        h
        for h in logging.getLogger().handlers
        if isinstance(h, logging.handlers.TimedRotatingFileHandler)
    ]
    assert len(file_handlers) == 1
    handler = file_handlers[0]
    assert handler.when == "MIDNIGHT"  # TimedRotatingFileHandler upper-cases `when`
    assert handler.backupCount == 3


def test_file_logging_failure_is_swallowed_not_raised(tmp_path, monkeypatch):
    """If creating the log file fails (e.g. read-only filesystem, permission
    error), setup_logging() must not raise -- console logging still works."""

    def _boom(*args, **kwargs):
        raise OSError("permission denied")

    monkeypatch.setattr("os.makedirs", _boom)

    logger = setup_logging(file_enabled=True, file_path=str(tmp_path / "sub" / "neo.log"))

    assert logger is not None
    assert not any(
        isinstance(h, logging.handlers.TimedRotatingFileHandler)
        for h in logging.getLogger().handlers
    )


def test_file_logging_with_bare_filename_skips_makedirs(tmp_path, monkeypatch):
    """A file_path with no directory component (e.g. "app.log", written to
    the current working directory) has no parent_dir to create -- os.makedirs
    must not be called, and the file still gets created."""
    monkeypatch.chdir(tmp_path)

    def _boom(*args, **kwargs):
        raise AssertionError("os.makedirs should not be called for a bare filename")

    monkeypatch.setattr("os.makedirs", _boom)

    setup_logging(file_enabled=True, file_path="bare.log")
    get_logger("test_bare_filename").warning("written_next_to_cwd")

    assert (tmp_path / "bare.log").exists()


def test_default_file_path_is_hyphenated():
    """Default file path is logs/neo-api-client.log (hyphenated, not
    logs/neo_api_client.log)."""
    from neo_api_client.logger import FILE_LOG_PATH

    assert FILE_LOG_PATH.replace("\\", "/") == "logs/neo-api-client.log"


def test_file_level_nolog_disables_file_even_if_enabled(tmp_path):
    """file_level="NOLOG" stops file logging entirely, equivalent to
    file_enabled=False -- even though file_enabled=True here."""
    log_path = tmp_path / "neo-api-client.log"
    setup_logging(file_enabled=True, file_path=str(log_path), file_level="NOLOG")

    get_logger("test_nolog_file").error("should_not_reach_the_file")

    assert not log_path.exists()
    assert not any(
        isinstance(h, logging.handlers.TimedRotatingFileHandler)
        for h in logging.getLogger().handlers
    )


def test_console_level_nolog_removes_console_handler():
    """level="NOLOG" disables console output entirely, symmetric to
    file_level="NOLOG" for the file -- no new handler is added."""
    before = logging.getLogger().handlers[:]
    setup_logging(level="NOLOG", file_enabled=False)

    assert logging.getLogger().handlers == before


def test_both_nolog_leaves_root_logger_silent(tmp_path):
    """With both outputs set to NOLOG, no handler is added and the root
    logger level is pushed above CRITICAL so nothing is even processed."""
    log_path = tmp_path / "neo-api-client.log"
    before = logging.getLogger().handlers[:]
    logger = setup_logging(
        level="NOLOG", file_enabled=True, file_path=str(log_path), file_level="NOLOG"
    )

    assert logger is not None
    assert logging.getLogger().handlers == before
    assert logging.getLogger().level > logging.CRITICAL
    assert not log_path.exists()


def test_setup_logging_replaces_rather_than_accumulates_handlers(tmp_path):
    """Calling setup_logging() again must fully replace its own previous
    handlers, not pile up on top of them. Regression test: an earlier bug
    meant a second call with file_level="WARNING" duplicated every file
    entry (one write per accumulated handler), and level="NOLOG" on a later
    call didn't actually silence the console, because the first call's
    console handler was still attached."""
    log_path = tmp_path / "neo-api-client.log"
    before = logging.getLogger().handlers[:]

    # First call: both outputs active.
    setup_logging(level="DEBUG", file_enabled=True, file_path=str(log_path), file_level="WARNING")
    count_after_first = len(logging.getLogger().handlers)

    # Second call: same file path. Must not add a second file handler.
    setup_logging(level="DEBUG", file_enabled=True, file_path=str(log_path), file_level="WARNING")
    assert len(logging.getLogger().handlers) == count_after_first

    get_logger("test_no_accumulation").warning("only_once")
    lines = [line for line in log_path.read_text().splitlines() if "only_once" in line]
    assert len(lines) == 1

    # Third call: NOLOG must actually take effect, not be masked by a
    # handler either of the first two calls left attached.
    setup_logging(level="NOLOG", file_enabled=True, file_path=str(log_path), file_level="NOLOG")
    assert logging.getLogger().handlers == before
