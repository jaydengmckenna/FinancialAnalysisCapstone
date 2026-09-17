"""Tests for application logging configuration."""

import logging
from pathlib import Path

from fin_automation.logging_config import (
    configure_logging,
    next_available_log_path,
)


def test_configure_logging_sets_requested_level() -> None:
    """Logging configuration should apply the requested level."""

    configure_logging(level=logging.DEBUG)

    root_logger = logging.getLogger()

    assert root_logger.level == logging.DEBUG
    assert len(root_logger.handlers) == 1
    assert root_logger.handlers[0].level == logging.DEBUG


def test_repeated_configuration_does_not_duplicate_handlers() -> None:
    """Repeated configuration should replace existing handlers."""

    configure_logging()
    configure_logging()

    root_logger = logging.getLogger()

    assert len(root_logger.handlers) == 1


def test_logging_writes_to_standard_output(capsys) -> None:
    """Configured logs should be written to standard output."""

    configure_logging(level=logging.INFO)

    logger = logging.getLogger("test_logger")
    logger.info("Configuration completed.")

    captured = capsys.readouterr()

    assert "Configuration completed." in captured.out
    assert "INFO" in captured.out
    assert "test_logger" in captured.out


def test_logging_redacts_known_secrets(capsys) -> None:
    """Configured secret values should not appear in logs."""

    secret = "example-sensitive-api-key"

    configure_logging(
        level=logging.INFO,
        secrets=[secret],
    )

    logger = logging.getLogger("test_logger")
    logger.info("Failed to use key %s", secret)

    captured = capsys.readouterr()

    assert secret not in captured.out
    assert "[REDACTED]" in captured.out


def test_configure_logging_without_log_file_uses_one_handler() -> None:
    """Omitting log_file should keep the console-only, single-handler default."""

    configure_logging(level=logging.INFO)

    root_logger = logging.getLogger()

    assert len(root_logger.handlers) == 1


def test_configure_logging_writes_to_log_file(tmp_path: Path) -> None:
    """A configured log_file should receive the same log records."""

    log_file = tmp_path / "logs" / "log1.txt"
    configure_logging(level=logging.INFO, log_file=log_file)

    root_logger = logging.getLogger()
    assert len(root_logger.handlers) == 2

    logger = logging.getLogger("test_logger")
    logger.info("Research plan created.")

    for handler in root_logger.handlers:
        handler.flush()

    assert log_file.is_file()
    contents = log_file.read_text(encoding="utf-8")
    assert "Research plan created." in contents
    assert "INFO" in contents


def test_configure_logging_redacts_secrets_in_log_file(tmp_path: Path) -> None:
    """Secret redaction should apply to the file handler too."""

    secret = "example-sensitive-api-key"
    log_file = tmp_path / "logs" / "log1.txt"
    configure_logging(level=logging.INFO, secrets=[secret], log_file=log_file)

    logger = logging.getLogger("test_logger")
    logger.info("Failed to use key %s", secret)

    for handler in logging.getLogger().handlers:
        handler.flush()

    contents = log_file.read_text(encoding="utf-8")
    assert secret not in contents
    assert "[REDACTED]" in contents


def test_next_available_log_path_returns_first_when_empty(
    tmp_path: Path,
) -> None:
    """An empty directory should get log1.txt."""

    assert next_available_log_path(tmp_path) == tmp_path / "log1.txt"


def test_next_available_log_path_skips_existing_files(
    tmp_path: Path,
) -> None:
    """An existing log1.txt should be skipped in favor of the next number."""

    (tmp_path / "log1.txt").write_text("existing", encoding="utf-8")
    (tmp_path / "log2.txt").write_text("existing", encoding="utf-8")

    assert next_available_log_path(tmp_path) == tmp_path / "log3.txt"
