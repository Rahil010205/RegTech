"""Qdrant collection schema definitions."""

from qdrant_client.models import Distance, VectorParams  # ← ADD THIS IMPORT

from app.core.config import get_settings
from app.core.constants import COLLECTION_REGULATORY_CLAUSES, COLLECTION_ORG_SECTIONS
from app.vectordb.qdrant_client import get_qdrant_client


def ensure_collections() -> None:
    """Create Qdrant collections if they do not exist."""
    settings = get_settings()
    client = get_qdrant_client()
    
    # Get existing collections
    collections = client.get_collections().collections
    existing_names = [c.name for c in collections]
    
    # Create regulatory clauses collection if missing
    if COLLECTION_REGULATORY_CLAUSES not in existing_names:
        client.create_collection(
            collection_name=COLLECTION_REGULATORY_CLAUSES,
            vectors_config=VectorParams(
                size=settings.embedding_dimension,  # 1024
                distance=Distance.COSINE,
            ),
        )
        print(f"✅ Created collection: {COLLECTION_REGULATORY_CLAUSES}")
    
    # Create org sections collection if missing (for Phase 4)
    if COLLECTION_ORG_SECTIONS not in existing_names:
        client.create_collection(
            collection_name=COLLECTION_ORG_SECTIONS,
            vectors_config=VectorParams(
                size=settings.embedding_dimension,  # 1024
                distance=Distance.COSINE,
            ),
        )
        print(f"✅ Created collection: {COLLECTION_ORG_SECTIONS}")