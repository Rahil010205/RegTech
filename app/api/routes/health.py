"""Health check endpoints — liveness and readiness probes."""

from fastapi import APIRouter

from app.api.schemas.common import HealthResponse, MessageResponse, ServiceStatus
from app.database.health import check_db_health, check_qdrant_health

router = APIRouter()


@router.get("", response_model=MessageResponse, summary="Liveness probe")
async def liveness() -> MessageResponse:
    """Returns 200 if the API process is running."""
    return MessageResponse(message="ok")


@router.get(
    "/ready",
    response_model=HealthResponse,
    summary="Readiness probe — checks DB and Qdrant connectivity",
)
async def readiness() -> HealthResponse:
    """Verifies PostgreSQL and Qdrant are reachable before signalling ready.

    Returns HTTP 200 with ``status="ok"`` when all dependencies are healthy,
    or ``status="degraded"`` when one or more are unreachable (still 200 so
    the response body can be inspected; callers should check the status field).
    """
    db_result = check_db_health()
    qdrant_result = check_qdrant_health()

    db_status = ServiceStatus(
        connected=db_result["ok"],
        error=db_result.get("error"),
    )
    qdrant_status = ServiceStatus(
        connected=qdrant_result["ok"],
        error=qdrant_result.get("error"),
    )

    overall = "ok" if db_status.connected and qdrant_status.connected else "degraded"

    return HealthResponse(
        status=overall,
        db=db_status,
        qdrant=qdrant_status,
    )
