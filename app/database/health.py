"""Database and Qdrant health-check helpers."""

import logging

from qdrant_client import QdrantClient
from sqlalchemy import text

from app.core.config import get_settings
from app.database.session import SessionLocal

logger = logging.getLogger(__name__)


def check_db_health() -> dict:
    """Try a lightweight query against PostgreSQL.

    Returns:
        ``{"ok": True}`` on success, ``{"ok": False, "error": "<msg>"}`` on failure.
    """
    try:
        session = SessionLocal()
        try:
            session.execute(text("SELECT 1"))
            return {"ok": True}
        finally:
            session.close()
    except Exception as exc:  # noqa: BLE001
        logger.warning("DB health check failed: %s", exc)
        return {"ok": False, "error": str(exc)}


def check_qdrant_health() -> dict:
    """Try listing Qdrant collections to verify connectivity.

    Returns:
        ``{"ok": True}`` on success, ``{"ok": False, "error": "<msg>"}`` on failure.
    """
    settings = get_settings()
    try:
        client = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key or None,
            timeout=settings.qdrant_timeout,
        )
        client.get_collections()
        return {"ok": True}
    except Exception as exc:  # noqa: BLE001
        logger.warning("Qdrant health check failed: %s", exc)
        return {"ok": False, "error": str(exc)}
