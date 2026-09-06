"""Application settings loaded from environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration — single source of truth for all modules."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="REGTECH_",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "RegTech Compliance API"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    secret_key: str = "change-me-in-production"

    # Database
    database_url: str = "postgresql+psycopg2://regtech:regtech@localhost:5432/regtech"
    db_pool_size: int = 10
    db_max_overflow: int = 20

    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str | None = None
    qdrant_timeout: int = 30

    # Embeddings
    embedding_provider: str = Field(default="local", description="local | openai")
    embedding_model_name: str = "BAAI/bge-large-en-v1.5"
    embedding_device: str = "cpu"
    embedding_batch_size: int = 32
    embedding_dimension: int = 1024
    openai_api_key: str | None = None
    openai_embedding_model: str = "text-embedding-3-small"

    # Celery
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"

    # Storage
    data_dir: Path = Path("./data")
    max_upload_bytes: int = Field(
        default=25 * 1024 * 1024,
        description="Maximum organization policy upload size in bytes",
    )

    # Retrieval
    retrieval_top_k: int = 5
    retrieval_top_k_max: int = 50
    rerank_top_k: int = 5
    similarity_threshold: float = 0.65
    matching_similarity_threshold: float = Field(
        default=0.60,
        description="Default cosine similarity threshold for regulatory-to-policy matching",
    )

    # Compliance
    mandatory_clause_threshold: float = 0.75

    # Risk Scoring Configuration (Step 3)
    risk_weight_compliance_severity: float = 0.40
    risk_weight_regulatory_criticality: float = 0.20
    risk_weight_gap_severity: float = 0.15
    risk_weight_evidence_strength: float = 0.15
    risk_weight_confidence: float = 0.10
    default_regulatory_criticality: str = "MEDIUM"

    @property
    def risk_weights(self) -> dict[str, float]:
        return {
            "compliance_severity": self.risk_weight_compliance_severity,
            "regulatory_criticality": self.risk_weight_regulatory_criticality,
            "gap_severity": self.risk_weight_gap_severity,
            "evidence_strength": self.risk_weight_evidence_strength,
            "confidence": self.risk_weight_confidence,
        }

    # LLM
    llm_provider: str = Field(default="openai", description="openai | mock")
    llm_model: str = "gpt-4o-mini"
    llm_api_key: str | None = None
    llm_temperature: float = 0.0
    llm_timeout_seconds: float = 30.0

    @property
    def effective_llm_api_key(self) -> str | None:
        return self.llm_api_key or self.openai_api_key

    # Logging
    log_level: str = "INFO"
    log_json: bool = False

    # Security (future auth)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    @property
    def raw_data_dir(self) -> Path:
        return self.data_dir / "raw"

    @property
    def processed_data_dir(self) -> Path:
        return self.data_dir / "processed"

    @property
    def reports_data_dir(self) -> Path:
        return self.data_dir / "reports"


@lru_cache
def get_settings() -> Settings:
    """Return cached settings singleton."""
    return Settings()
