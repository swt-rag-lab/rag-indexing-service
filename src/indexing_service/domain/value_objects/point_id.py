"""PointId value object — deterministic UUID for a Qdrant point."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

# Fixed namespace for point ID generation
_POINT_NAMESPACE = uuid.UUID("f0e1d2c3-b4a5-6789-0123-456789abcdef")


@dataclass(frozen=True)
class PointId:
    """Deterministic identifier for a vector point in Qdrant.

    Generated from (tenant_id, document_id, version_id, chunk_index) to
    guarantee idempotent upserts — same inputs always produce the same point_id.
    """

    value: str

    @classmethod
    def generate(
        cls,
        tenant_id: str,
        document_id: uuid.UUID,
        version_id: uuid.UUID,
        chunk_index: int,
    ) -> PointId:
        """Generate a deterministic PointId.

        Same inputs always produce the same PointId.
        """
        name = f"{tenant_id}:{document_id}:{version_id}:{chunk_index}"
        point_uuid = uuid.uuid5(_POINT_NAMESPACE, name)
        return cls(value=str(point_uuid))

    def __str__(self) -> str:
        return self.value
