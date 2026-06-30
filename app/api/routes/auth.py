"""Authentication endpoints (future-ready stubs)."""

from fastapi import APIRouter, status

from app.api.schemas.common import MessageResponse

router = APIRouter()


@router.post("/login", response_model=MessageResponse, status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def login() -> MessageResponse:
  """Authenticate user and return JWT access token. Not yet implemented."""
  return MessageResponse(message="Auth not yet implemented")


@router.post("/refresh", response_model=MessageResponse, status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def refresh_token() -> MessageResponse:
  """Refresh an expired access token. Not yet implemented."""
  return MessageResponse(message="Auth not yet implemented")
