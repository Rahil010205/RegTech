"""Batch vector upsert to Qdrant."""

from typing import Any

from qdrant_client.models import PointStruct  # ← ADD THIS IMPORT

from app.vectordb.qdrant_client import get_qdrant_client


class VectorUploader:
    """Upload clause embeddings to Qdrant with idempotency."""

    def upsert(
        self,
        collection: str,
        ids: list,
        vectors: list[list[float]],
        payloads: list[dict[str, Any]],
    ) -> None:
        """Batch upsert points to Qdrant."""
        if not ids:
            return
        
        client = get_qdrant_client()
        
        points = [
            PointStruct(
                id=str(id_),
                vector=vector,
                payload=payload,
            )
            for id_, vector, payload in zip(ids, vectors, payloads)
        ]
        
        # Upsert in batches for better performance
        batch_size = 64
        for i in range(0, len(points), batch_size):
            batch = points[i:i+batch_size]
            client.upsert(
                collection_name=collection,
                points=batch,
                wait=True,
            )
        
        print(f"✅ Upserted {len(points)} points to {collection}")