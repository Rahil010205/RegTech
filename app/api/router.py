"""Aggregates all API route modules."""

from fastapi import APIRouter

from app.api.routes import auth, compliance, documents, health, organizations, regulations, reports, search

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(organizations.router, prefix="/organizations", tags=["Organizations"])
api_router.include_router(regulations.router, prefix="/regulations", tags=["Regulations"])
api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_router.include_router(compliance.router, prefix="/compliance", tags=["Compliance"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_router.include_router(search.router, prefix="/search", tags=["Search"])
