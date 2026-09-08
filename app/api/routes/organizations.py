"""Organization and organization-policy document endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from fastapi.responses import JSONResponse

from app.api.dependencies.services import (
    get_compliance_analysis_service,
    get_compliance_risk_scoring_service,
    get_document_compliance_service,
    get_organization_policy_service,
    get_regulatory_policy_matching_service,
)
from app.api.schemas.compliance_analysis import (
    ComplianceAnalysisRequest,
    ComplianceAnalysisResponse,
)
from app.api.schemas.document_compliance import (
    DocumentComplianceRequest,
    DocumentComplianceReportResponse,
)
from app.api.schemas.matching import (
    RegulatoryPolicyMatchRequest,
    RegulatoryPolicyMatchResponse,
)
from app.api.schemas.organization_document import (
    OrganizationCreateRequest,
    OrganizationDocumentIngestResponse,
    OrganizationPolicySearchRequest,
    OrganizationPolicySearchResponse,
    OrganizationResponse,
)
from app.api.schemas.risk_scoring import (
    RiskScoringRequest,
    RiskScoringResponse,
)
from app.core.constants import OrganizationDocumentStatus
from app.services.compliance_analysis import ComplianceAnalysisService
from app.services.compliance_risk_scoring import ComplianceRiskScoringService
from app.services.document_compliance_service import DocumentComplianceService
from app.services.organization_policy_service import OrganizationPolicyService
from app.services.regulatory_policy_matching import RegulatoryPolicyMatchingService

router = APIRouter()


@router.post("", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
def create_organization(
    payload: OrganizationCreateRequest,
    service: Annotated[OrganizationPolicyService, Depends(get_organization_policy_service)],
) -> OrganizationResponse:
    """Create a new organization tenant."""
    return service.create_organization(payload)


@router.get("/{organization_id}", response_model=OrganizationResponse)
def get_organization(
    organization_id: UUID,
    service: Annotated[OrganizationPolicyService, Depends(get_organization_policy_service)],
) -> OrganizationResponse:
    """Get organization by ID."""
    return service.get_organization(organization_id)


@router.post(
    "/{organization_id}/documents",
    response_model=OrganizationDocumentIngestResponse,
    summary="Upload and ingest an organization policy PDF",
)
async def upload_organization_document(
    organization_id: UUID,
    service: Annotated[OrganizationPolicyService, Depends(get_organization_policy_service)],
    file: UploadFile = File(..., description="Organization policy PDF"),
    document_type: str | None = Form(default=None),
    version: str | None = Form(default=None),
) -> OrganizationDocumentIngestResponse | JSONResponse:
    """Ingest an organization policy PDF into pgvector-backed policy chunks."""
    content = await file.read()
    result = service.upload_document(
        organization_id=organization_id,
        filename=file.filename or "upload.pdf",
        content=content,
        document_type=document_type,
        version=version,
    )
    if result.status == OrganizationDocumentStatus.FAILED.value:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=result.model_dump(mode="json"),
        )
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=result.model_dump(mode="json"),
    )


@router.post(
    "/{organization_id}/documents/search",
    response_model=OrganizationPolicySearchResponse,
    summary="Semantic search over organization policy chunks",
)
def search_organization_policies(
    organization_id: UUID,
    request: OrganizationPolicySearchRequest,
    service: Annotated[OrganizationPolicyService, Depends(get_organization_policy_service)],
) -> OrganizationPolicySearchResponse:
    """Search only the specified organization's ingested policy chunks."""
    return service.search(
        organization_id=organization_id,
        query=request.query,
        top_k=request.top_k,
        min_similarity=request.min_similarity,
    )


@router.post(
    "/{organization_id}/compliance/match",
    response_model=RegulatoryPolicyMatchResponse,
    summary="Match a regulatory clause to organization policy chunks",
    description=(
        "Reuse the stored regulatory clause embedding and retrieve the most "
        "semantically similar policy chunks for the specified organization. "
        "This endpoint returns evidence only; it does not decide compliance."
    ),
)
def match_regulatory_clause_to_policy(
    organization_id: UUID,
    request: RegulatoryPolicyMatchRequest,
    service: Annotated[
        RegulatoryPolicyMatchingService,
        Depends(get_regulatory_policy_matching_service),
    ],
) -> RegulatoryPolicyMatchResponse:
    """Find organization-policy evidence for one regulatory clause."""
    return service.match_regulatory_clause_to_policy(
        organization_id=organization_id,
        regulatory_clause_id=request.regulatory_clause_id,
        top_k=request.top_k,
        similarity_threshold=request.similarity_threshold,
    )


@router.post(
    "/{organization_id}/compliance/analyze",
    response_model=ComplianceAnalysisResponse,
    summary="Analyze regulatory compliance of organization policies via LLM",
    description=(
        "Retrieve relevant organization policy evidence via Step 2A pgvector semantic "
        "matching and analyze compliance status using an LLM."
    ),
)
def analyze_compliance(
    organization_id: UUID,
    request: ComplianceAnalysisRequest,
    service: Annotated[
        ComplianceAnalysisService,
        Depends(get_compliance_analysis_service),
    ],
) -> ComplianceAnalysisResponse:
    """Evaluate organization policy compliance for a single regulatory clause using LLM analysis."""
    return service.analyze(
        organization_id=organization_id,
        regulatory_clause_id=request.regulatory_clause_id,
        top_k=request.top_k,
        similarity_threshold=request.similarity_threshold,
    )


@router.post(
    "/{organization_id}/compliance/risk",
    response_model=RiskScoringResponse,
    summary="Assess regulatory compliance risk score and severity",
    description=(
        "Evaluate regulatory compliance of organization policies via Step 2A/2B and "
        "compute a deterministic, explainable risk score (0–100) and severity level."
    ),
)
def evaluate_compliance_risk(
    organization_id: UUID,
    request: RiskScoringRequest,
    service: Annotated[
        ComplianceRiskScoringService,
        Depends(get_compliance_risk_scoring_service),
    ],
) -> RiskScoringResponse:
    """Compute deterministic compliance risk score and factor breakdown for an organization."""
    return service.evaluate_risk(
        organization_id=organization_id,
        regulatory_clause_id=request.regulatory_clause_id,
        top_k=request.top_k,
        similarity_threshold=request.similarity_threshold,
    )


@router.post(
    "/{organization_id}/documents/{policy_document_id}/compliance-analysis",
    response_model=DocumentComplianceReportResponse,
    summary="Run document-level compliance analysis for an organization policy document",
)
def analyze_document_compliance(
    organization_id: UUID,
    policy_document_id: UUID,
    request: DocumentComplianceRequest,
    service: Annotated[
        DocumentComplianceService,
        Depends(get_document_compliance_service),
    ],
) -> DocumentComplianceReportResponse:
    """Analyze all policy clauses in a document against relevant regulatory requirements."""
    payload = service.analyze_document(
        organization_id=organization_id,
        policy_document_id=policy_document_id,
        top_k=request.top_k,
        similarity_threshold=request.similarity_threshold,
    )
    return DocumentComplianceReportResponse.model_validate(payload)


@router.get(
    "/{organization_id}/documents/{policy_document_id}/compliance-report",
    response_model=DocumentComplianceReportResponse,
    summary="Get previously generated document-level compliance report",
)
def get_document_compliance_report(
    organization_id: UUID,
    policy_document_id: UUID,
    service: Annotated[
        DocumentComplianceService,
        Depends(get_document_compliance_service),
    ],
) -> DocumentComplianceReportResponse:
    """Retrieve the persisted document-level compliance report for an organization policy document."""
    return service.list_reports(
        organization_id=organization_id,
        policy_document_id=policy_document_id,
    )

