"""ChunkId value object — deterministic UUID for a chunk."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

# Fixed namespace for chunk ID generation
_CHUNK_NAMESPACE = uuid.UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")


@dataclass(frozen=True)
class ChunkId:
    """Deterministic identifier for a chunk.

    Generated from (document_id, version_id, chunk_index) to ensure
    the same chunk always gets the same ID.
    """

    value: uuid.UUID

    @classmethod
    def generate(
        cls,
        document_id: uuid.UUID,
        version_id: uuid.UUID,
        chunk_index: int,
    ) -> ChunkId:
        """Generate a deterministic ChunkId.

        Same inputs always produce the same ChunkId.
        """
        name = f"{document_id}:{version_id}:{chunk_index}"
        return cls(value=uuid.uuid5(_CHUNK_NAMESPACE, name))

    def __str__(self) -> str:
        return str(self.value)
