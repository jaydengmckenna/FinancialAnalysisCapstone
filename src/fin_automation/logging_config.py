"""Logging configuration for the application."""

import logging
import sys
from collections.abc import Iterable


DEFAULT_LOG_FORMAT = (
    "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)


class SecretRedactionFilter(logging.Filter):
    """Remove known secret values from log records."""

    def __init__(self, secrets: Iterable[str] | None = None) -> None:
        """Initialize the filter with secret values to redact."""

        super().__init__()

        self._secrets = tuple(
            secret
            for secret in (secrets or [])
            if secret
        )

    def filter(self, record: logging.LogRecord) -> bool:
        """Redact configured secret values from a log message."""

        message = record.getMessage()

        for secret in self._secrets:
            message = message.replace(secret, "[REDACTED]")

        record.msg = message
        record.args = ()

        return True


def configure_logging(
    level: int = logging.INFO,
    secrets: Iterable[str] | None = None,
) -> None:
    """Configure application logging to standard output."""

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    root_logger.handlers.clear()

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(
        logging.Formatter(DEFAULT_LOG_FORMAT)
    )
    console_handler.addFilter(
        SecretRedactionFilter(secrets=secrets)
    )

    root_logger.addHandler(console_handler)