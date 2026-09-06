"""Application-wide constants and enumerations."""

from enum import StrEnum


class RegulatorCode(StrEnum):
    """Supported regulatory bodies."""

    RBI = "RBI"
    SEBI = "SEBI"
    IRDAI = "IRDAI"
    GDPR = "GDPR"
    ISO = "ISO"


class DocumentType(StrEnum):
    """Document classification types."""

    CIRCULAR = "circular"
    GUIDELINE = "guideline"
    ACT = "act"
    POLICY = "policy"
    SOP = "sop"
    PROCEDURE = "procedure"


class IngestionStatus(StrEnum):
    """Async ingestion job states."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class OrganizationDocumentStatus(StrEnum):
    """Organization policy document processing states."""

    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class OrganizationDocumentType(StrEnum):
    """Common organization policy document classifications."""

    KYC_POLICY = "KYC_POLICY"
    AML_POLICY = "AML_POLICY"
    COMPLIANCE_MANUAL = "COMPLIANCE_MANUAL"
    SOP = "SOP"
    RISK_POLICY = "RISK_POLICY"
    PROCEDURE = "PROCEDURE"
    OTHER = "OTHER"


class ComplianceStatus(StrEnum):
    """Per-clause compliance outcome."""

    COMPLIANT = "compliant"
    PARTIAL = "partial"
    NON_COMPLIANT = "non_compliant"
    NOT_APPLICABLE = "not_applicable"


class RiskLevel(StrEnum):
    """Risk severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskScoreLevel(StrEnum):
    """Deterministic risk levels for Step 3 compliance scoring."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class GapSeverity(StrEnum):
    """Gap severity classifications."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RegulatoryCriticality(StrEnum):
    """Regulatory requirement criticality classifications."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class JobStatus(StrEnum):
    """Generic async job status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# Qdrant collection names
COLLECTION_REGULATORY_CLAUSES = "regulatory_clauses"
COLLECTION_ORG_SECTIONS = "org_document_sections"

# Celery queue names
QUEUE_INGESTION = "ingestion"
QUEUE_EMBEDDING = "embedding"
QUEUE_COMPLIANCE = "compliance"
QUEUE_REPORTS = "reports"

# BGE model query prefix
BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "
