"""Domain and infrastructure exception hierarchy."""


class RegTechError(Exception):
    """Base exception for all RegTech errors."""

    def __init__(self, message: str, error_code: str = "INTERNAL_ERROR") -> None:
        self.message = message
        self.error_code = error_code
        super().__init__(message)


# --- Domain errors ---


class DomainError(RegTechError):
    """Business rule violation."""


class ValidationError(DomainError):
    """Input or parsed data failed validation."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message, "VALIDATION_ERROR")
        self.details = details or {}


class ClauseParsingError(DomainError):
    """PDF or clause extraction failed."""

    def __init__(self, message: str) -> None:
        super().__init__(message, "CLAUSE_PARSING_FAILED")


class IngestionError(DomainError):
    """Regulatory document ingestion failed."""

    def __init__(self, message: str, error_code: str = "INGESTION_FAILED") -> None:
        super().__init__(message, error_code)


class EmptyDocumentError(IngestionError):
    def __init__(self, message: str = "Document contains no extractable text") -> None:
        super().__init__(message, "EMPTY_DOCUMENT")


class DuplicateDocumentError(IngestionError):
    def __init__(self, message: str, document_id: str | None = None) -> None:
        super().__init__(message, "DUPLICATE_DOCUMENT")
        self.document_id = document_id


class ComplianceEvaluationError(DomainError):
    """Compliance evaluation could not complete."""

    def __init__(self, message: str) -> None:
        super().__init__(message, "COMPLIANCE_EVALUATION_FAILED")


# --- Infrastructure errors ---


class InfrastructureError(RegTechError):
    """External system failure."""


class DatabaseError(InfrastructureError):
    def __init__(self, message: str) -> None:
        super().__init__(message, "DATABASE_ERROR")


class VectorStoreError(InfrastructureError):
    def __init__(self, message: str) -> None:
        super().__init__(message, "VECTOR_STORE_ERROR")


class EmbeddingModelError(InfrastructureError):
    def __init__(self, message: str) -> None:
        super().__init__(message, "EMBEDDING_MODEL_ERROR")


class LLMError(InfrastructureError):
    """Base exception for LLM provider errors."""

    def __init__(self, message: str, error_code: str = "LLM_ERROR") -> None:
        super().__init__(message, error_code)


class LLMTimeoutError(LLMError):
    def __init__(self, message: str = "LLM request timed out") -> None:
        super().__init__(message, "LLM_TIMEOUT")


class LLMServiceError(LLMError):
    def __init__(self, message: str = "Compliance analysis service is temporarily unavailable.") -> None:
        super().__init__(message, "LLM_SERVICE_UNAVAILABLE")


class LLMResponseValidationError(ComplianceEvaluationError):
    def __init__(self, message: str = "LLM response failed validation") -> None:
        super().__init__(message)


# --- Application errors ---


class ApplicationError(RegTechError):
    """Application-level errors (not found, conflict, auth)."""


class NotFoundError(ApplicationError):
    def __init__(self, resource: str, identifier: str) -> None:
        super().__init__(f"{resource} '{identifier}' not found", "NOT_FOUND")
        self.resource = resource
        self.identifier = identifier


class ConflictError(ApplicationError):
    def __init__(self, message: str) -> None:
        super().__init__(message, "CONFLICT")


class UnauthorizedError(ApplicationError):
    def __init__(self, message: str = "Unauthorized") -> None:
        super().__init__(message, "UNAUTHORIZED")
