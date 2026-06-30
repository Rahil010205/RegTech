"""Global exception handler registration."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import (
  ApplicationError,
  DomainError,
  InfrastructureError,
  NotFoundError,
  RegTechError,
  UnauthorizedError,
  ValidationError,
)


def register_exception_handlers(app: FastAPI) -> None:
  @app.exception_handler(NotFoundError)
  async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    return _error_response(request, exc, 404)

  @app.exception_handler(ValidationError)
  async def validation_handler(request: Request, exc: ValidationError) -> JSONResponse:
    return _error_response(request, exc, 422, details=exc.details)

  @app.exception_handler(UnauthorizedError)
  async def unauthorized_handler(request: Request, exc: UnauthorizedError) -> JSONResponse:
    return _error_response(request, exc, 401)

  @app.exception_handler(DomainError)
  async def domain_handler(request: Request, exc: DomainError) -> JSONResponse:
    return _error_response(request, exc, 400)

  @app.exception_handler(InfrastructureError)
  async def infra_handler(request: Request, exc: InfrastructureError) -> JSONResponse:
    return _error_response(request, exc, 503)

  @app.exception_handler(RegTechError)
  async def regtech_handler(request: Request, exc: RegTechError) -> JSONResponse:
    return _error_response(request, exc, 500)


def _error_response(
  request: Request,
  exc: RegTechError,
  status_code: int,
  details: dict | None = None,
) -> JSONResponse:
  request_id = getattr(request.state, "request_id", None)
  return JSONResponse(
    status_code=status_code,
    content={
      "error_code": exc.error_code,
      "message": exc.message,
      "details": details or {},
      "request_id": request_id,
    },
  )
