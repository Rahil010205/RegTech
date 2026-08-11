"""Standard-library logging configuration for the RegTech platform.

Uses Python's built-in `logging` module (not loguru) with a structured
formatter that includes timestamp, level, logger name, and message.
"""

import logging
import logging.handlers
import sys
from pathlib import Path

from app.core.config import get_settings


class _StructuredFormatter(logging.Formatter):
    """Human-readable formatter: timestamp | level | name | message."""

    FMT = "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s"
    DATE_FMT = "%Y-%m-%d %H:%M:%S"

    def __init__(self) -> None:
        super().__init__(fmt=self.FMT, datefmt=self.DATE_FMT)


def setup_logging() -> None:
    """Configure root logger with console + rotating file sinks.

    Call once at application startup (inside the FastAPI lifespan hook).
    Subsequent calls are idempotent — handlers are not duplicated.
    """
    settings = get_settings()
    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    root = logging.getLogger()

    # Avoid adding duplicate handlers on repeated calls (e.g. --reload)
    if root.handlers:
        return

    root.setLevel(level)

    formatter = _StructuredFormatter()

    # --- Console sink ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root.addHandler(console_handler)

    # --- Rotating file sink (daily, keep 30 days) ---
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename=log_dir / "regtech.log",
        when="midnight",
        backupCount=30,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    root.info("Logging initialised — level=%s", settings.log_level)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger for a module.

    Usage::

        logger = get_logger(__name__)
        logger.info("Something happened")
    """
    return logging.getLogger(name)
