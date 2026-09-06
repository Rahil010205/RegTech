"""Service factory dependencies."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.dependencies.db import get_db
from app.services.compliance_service import ComplianceService
from app.services.document_service import DocumentService
from app.services.organization_policy_service import OrganizationPolicyService
from app.services.regulation_service import RegulationService
from app.services.report_service import ReportService
from app.services.compliance_analysis import ComplianceAnalysisService
from app.services.compliance_risk_scoring import ComplianceRiskScoringService
from app.services.regulatory_policy_matching import RegulatoryPolicyMatchingService
from app.services.search_service import SearchService


def get_regulation_service(db: Annotated[Session, Depends(get_db)]) -> RegulationService:
  return RegulationService(db)


def get_document_service(db: Annotated[Session, Depends(get_db)]) -> DocumentService:
  return DocumentService(db)


def get_compliance_service(db: Annotated[Session, Depends(get_db)]) -> ComplianceService:
  return ComplianceService(db)


def get_report_service(db: Annotated[Session, Depends(get_db)]) -> ReportService:
  return ReportService(db)


def get_search_service(db: Annotated[Session, Depends(get_db)]) -> SearchService:
  return SearchService(db)


def get_organization_policy_service(
    db: Annotated[Session, Depends(get_db)],
) -> OrganizationPolicyService:
    return OrganizationPolicyService(db)


def get_regulatory_policy_matching_service(
    db: Annotated[Session, Depends(get_db)],
) -> RegulatoryPolicyMatchingService:
    return RegulatoryPolicyMatchingService(db)


def get_compliance_analysis_service(
    matching_service: Annotated[RegulatoryPolicyMatchingService, Depends(get_regulatory_policy_matching_service)],
) -> ComplianceAnalysisService:
    return ComplianceAnalysisService(matching_service=matching_service)


def get_compliance_risk_scoring_service(
    compliance_analysis_service: Annotated[
        ComplianceAnalysisService,
        Depends(get_compliance_analysis_service),
    ],
    db: Annotated[Session, Depends(get_db)],
) -> ComplianceRiskScoringService:
    return ComplianceRiskScoringService(
        compliance_analysis_service=compliance_analysis_service,
        db_session=db,
    )
