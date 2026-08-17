"""VectorStore port — interface for vector storage operations."""

from __future__ import annotations

from typing import Protocol

from indexing_service.domain.ports.vector_point import VectorPoint


class VectorStore(Protocol):
    """Port for storing and managing vectors.

    Implementations may use Qdrant, Pinecone, pgvector, etc.
    The domain does not know which store is used.
    """

    async def upsert_points(self, points: list[VectorPoint]) -> None:
        """Upsert points (vectors + payloads) to the store.

        Idempotent: same point_id replaces the existing point.
        """
        ...

    async def delete_points_by_document(
        self,
        tenant_id: str,
        document_id: str,
        version_id: str,
    ) -> int:
        """Delete all points for a specific document version.

        Returns:
            Count of points deleted.
        """
        ...

    async def ensure_collection(self, dimensions: int) -> None:
        """Ensure the collection exists with correct configuration."""
        ...

    async def health_check(self) -> bool:
        """Check if the vector store is reachable."""
        ...
