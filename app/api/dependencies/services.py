"""Service factory dependencies."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.dependencies.db import get_db
from app.services.compliance_service import ComplianceService
from app.services.document_service import DocumentService
from app.services.regulation_service import RegulationService
from app.services.report_service import ReportService


def get_regulation_service(db: Annotated[Session, Depends(get_db)]) -> RegulationService:
  return RegulationService(db)


def get_document_service(db: Annotated[Session, Depends(get_db)]) -> DocumentService:
  return DocumentService(db)


def get_compliance_service(db: Annotated[Session, Depends(get_db)]) -> ComplianceService:
  return ComplianceService(db)


def get_report_service(db: Annotated[Session, Depends(get_db)]) -> ReportService:
  return ReportService(db)
