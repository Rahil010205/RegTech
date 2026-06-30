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
    embedding_model_name: str = "BAAI/bge-large-en-v1.5"
    embedding_device: str = "cpu"
    embedding_batch_size: int = 32
    embedding_dimension: int = 1024

    # Celery
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"

    # Storage
    data_dir: Path = Path("./data")

    # Retrieval
    retrieval_top_k: int = 10
    rerank_top_k: int = 5
    similarity_threshold: float = 0.65

    # Compliance
    mandatory_clause_threshold: float = 0.75

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
