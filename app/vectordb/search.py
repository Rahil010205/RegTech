"""Vector similarity search."""

from typing import Any

from qdrant_client.models import FieldCondition, Filter, MatchValue  # ← ADD THIS IMPORT

from app.vectordb.qdrant_client import get_qdrant_client


class VectorSearch:
    """Semantic search with payload filtering."""

    def search(
        self,
        collection: str,
        query_vector: list[float],
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Search collection with optional payload filters."""
        client = get_qdrant_client()
        
        # Build Qdrant filter from dict
        qdrant_filter = None
        if filters:
            conditions = []
            for key, value in filters.items():
                if isinstance(value, list):
                    # Support IN operator (e.g., regulator: ["RBI", "SEBI"])
                    for v in value:
                        conditions.append(
                            FieldCondition(
                                key=key,
                                match=MatchValue(value=v),
                            )
                        )
                else:
                    # Single value match
                    conditions.append(
                        FieldCondition(
                            key=key,
                            match=MatchValue(value=value),
                        )
                    )
            if conditions:
                qdrant_filter = Filter(must=conditions)
        
        # Execute search
        results = client.search(
            collection_name=collection,
            query_vector=query_vector,
            limit=top_k,
            query_filter=qdrant_filter,
            with_payload=True,
        )
        
        # Return payload + score + id
        return [
            {
                **hit.payload,
                "score": hit.score,
                "id": hit.id,
            }
            for hit in results
        ]