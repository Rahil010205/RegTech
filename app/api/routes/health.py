"""Health check endpoints."""

from fastapi import APIRouter

from app.api.schemas.common import MessageResponse

router = APIRouter()


@router.get("", response_model=MessageResponse, summary="Liveness probe")
async def liveness() -> MessageResponse:
  """Returns 200 if the API process is running."""
  return MessageResponse(message="ok")


@router.get("/ready", response_model=MessageResponse, summary="Readiness probe")
async def readiness() -> MessageResponse:
  """
  Returns 200 when all dependencies (PostgreSQL, Qdrant, Redis) are reachable.

  TODO: Add actual connectivity checks before production deployment.
  """
  return MessageResponse(message="ready")
