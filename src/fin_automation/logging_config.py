"""Logging configuration for the application."""

import logging
from pathlib import Path
import sys
from collections.abc import Iterable


DEFAULT_LOG_FORMAT = (
    "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

# Third-party libraries that log routine HTTP traffic at INFO level.
# Configuring the root logger affects every logger in the process, so
# without this every outbound API call would also appear in the log,
# burying the application's own stage-by-stage messages in noise.
_NOISY_THIRD_PARTY_LOGGERS = (
    "httpx",
    "httpx2",
    "httpcore",
    "openai",
    "urllib3",
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


def next_available_log_path(log_directory: Path) -> Path:
    """Return log1.txt or the next available numbered filename.

    Mirrors `ReportWriterTool._next_available_path`, so runtime logs
    and report artifacts follow the same collision-safe naming
    convention without overwriting a previous run's log.
    """

    counter = 1
    while True:
        log_path = log_directory / f"log{counter}.txt"
        if not log_path.exists():
            return log_path
        counter += 1


def configure_logging(
    level: int = logging.INFO,
    secrets: Iterable[str] | None = None,
    log_file: Path | None = None,
) -> None:
    """Configure application logging to standard output.

    Args:
        level: Logging level applied to every handler.
        secrets: Known secret values to redact from log messages.
        log_file: Optional file path to also write logs to, in
            addition to standard output. The parent directory is
            created if needed. Runtime logs are written separately
            from permanent report artifacts even though both may live
            under the same output directory (e.g. `outputs/logs/` vs
            `outputs/report1.md`).
    """

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    root_logger.handlers.clear()

    formatter = logging.Formatter(DEFAULT_LOG_FORMAT)
    redaction_filter = SecretRedactionFilter(secrets=secrets)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(redaction_filter)
    root_logger.addHandler(console_handler)

    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        file_handler.addFilter(redaction_filter)
        root_logger.addHandler(file_handler)

    for logger_name in _NOISY_THIRD_PARTY_LOGGERS:
        logging.getLogger(logger_name).setLevel(logging.WARNING)