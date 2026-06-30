"""Authentication dependencies (future-ready)."""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer(auto_error=False)


class CurrentUser:
  """Placeholder user context until auth is implemented."""

  def __init__(self, user_id: UUID | None = None, org_id: UUID | None = None, role: str = "admin") -> None:
    self.user_id = user_id
    self.org_id = org_id
    self.role = role


async def get_current_user(
  credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> CurrentUser:
  """
  Validate JWT and return current user.

  Currently returns a stub admin user when no token is provided (dev mode).
  Replace with real JWT validation before production.
  """
  if credentials is None:
    return CurrentUser()
  # TODO: decode token via app.core.security.decode_access_token
  raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Auth not yet implemented")


def require_role(*roles: str):
  """Dependency factory that enforces role-based access."""

  async def _check(user: Annotated[CurrentUser, Depends(get_current_user)]) -> CurrentUser:
    if user.role not in roles:
      raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    return user

  return _check
