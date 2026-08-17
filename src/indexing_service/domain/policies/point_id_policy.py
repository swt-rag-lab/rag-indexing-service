"""PointIdPolicy — deterministic generation of Qdrant point IDs."""

from __future__ import annotations

import uuid

from indexing_service.domain.value_objects.point_id import PointId


class PointIdPolicy:
    """Policy for generating deterministic Qdrant point IDs.

    Guarantees: same (tenant_id, document_id, version_id, chunk_index) → same point_id.
    This ensures idempotent upserts in Qdrant.
    """

    @staticmethod
    def generate(
        tenant_id: str,
        document_id: uuid.UUID,
        version_id: uuid.UUID,
        chunk_index: int,
    ) -> PointId:
        """Generate a deterministic PointId.

        Args:
            tenant_id: Tenant identifier.
            document_id: Document UUID.
            version_id: Document version UUID.
            chunk_index: Zero-based chunk index.

        Returns:
            Deterministic PointId.
        """
        return PointId.generate(
            tenant_id=tenant_id,
            document_id=document_id,
            version_id=version_id,
            chunk_index=chunk_index,
        )
