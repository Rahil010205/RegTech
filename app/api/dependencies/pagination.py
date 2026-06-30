"""Pagination dependency."""

from fastapi import Query

from app.api.schemas.common import PaginationParams


def get_pagination(
  skip: int = Query(0, ge=0),
  limit: int = Query(50, ge=1, le=100),
) -> PaginationParams:
  return PaginationParams(skip=skip, limit=limit)
