"""Tests for application logging configuration."""

import logging

from fin_automation.logging_config import configure_logging


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

    