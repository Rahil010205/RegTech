"""Loguru logging configuration."""

import sys

from loguru import logger

from app.core.config import get_settings


def setup_logging() -> None:
    """Configure loguru sinks and format. Call once at application startup."""
    settings = get_settings()
    logger.remove()

    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{extra[request_id]}</cyan> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    logger.configure(extra={"request_id": "-"})
    logger.add(
        sys.stdout,
        format=log_format,
        level=settings.log_level,
        serialize=settings.log_json,
    )
    logger.add(
        "logs/regtech_{time:YYYY-MM-DD}.log",
        rotation="00:00",
        retention="30 days",
        level=settings.log_level,
        serialize=settings.log_json,
    )


def get_logger(name: str):
    """Return a bound logger for a module."""
    return logger.bind(module=name)
