"""Chunk entity — represents a chunk of a document with full metadata."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from indexing_service.domain.value_objects.chunk_id import ChunkId
from indexing_service.domain.value_objects.content_hash import ContentHash
from indexing_service.domain.value_objects.point_id import PointId
from indexing_service.domain.value_objects.tenant_id import TenantId


@dataclass(frozen=True)
class SourceMetadata:
    """Metadata tracing a chunk back to its origin document and processing pipeline."""

    source_content_type: str
    source_content_hash: str
    extractor_type: str
    extractor_version: str
    embedding_model: str
    chunking_version: str


@dataclass(frozen=True)
class StructuralMetadata:
    """Structural metadata extracted from the document's markdown content."""

    section_type: str | None = None
    section_title: str | None = None
    page_start: int | None = None
    page_end: int | None = None
    hierarchy: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Chunk:
    """Entity representing a chunk of a document with full traceability.

    Immutable once created. Contains content, position, deterministic IDs,
    and rich metadata for tracing back to the source document.
    """

    id: ChunkId
    tenant_id: TenantId
    document_id: uuid.UUID
    version_id: uuid.UUID
    chunk_index: int
    content: str
    token_count: int
    content_hash: ContentHash
    point_id: PointId
    start_token: int
    end_token: int
    has_overlap: bool
    forced_split: bool
    source_metadata: SourceMetadata
    structural_metadata: StructuralMetadata
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        """Validate invariants."""
        if self.chunk_index < 0:
            msg = f"chunk_index must be >= 0, got {self.chunk_index}"
            raise ValueError(msg)
        if self.token_count <= 0:
            msg = f"token_count must be > 0, got {self.token_count}"
            raise ValueError(msg)
        if not self.content:
            msg = "Chunk content must not be empty."
            raise ValueError(msg)
        if self.start_token < 0:
            msg = f"start_token must be >= 0, got {self.start_token}"
            raise ValueError(msg)
        if self.end_token <= self.start_token:
            msg = f"end_token ({self.end_token}) must be > start_token ({self.start_token})"
            raise ValueError(msg)

    @classmethod
    def create(
        cls,
        *,
        tenant_id: TenantId,
        document_id: uuid.UUID,
        version_id: uuid.UUID,
        chunk_index: int,
        content: str,
        token_count: int,
        start_token: int,
        end_token: int,
        has_overlap: bool,
        forced_split: bool,
        source_metadata: SourceMetadata,
        structural_metadata: StructuralMetadata,
    ) -> Chunk:
        """Factory method: creates a Chunk with deterministic IDs and computed hash."""
        chunk_id = ChunkId.generate(document_id, version_id, chunk_index)
        point_id = PointId.generate(
            tenant_id=str(tenant_id),
            document_id=document_id,
            version_id=version_id,
            chunk_index=chunk_index,
        )
        content_hash = ContentHash.from_text(content)

        return cls(
            id=chunk_id,
            tenant_id=tenant_id,
            document_id=document_id,
            version_id=version_id,
            chunk_index=chunk_index,
            content=content,
            token_count=token_count,
            content_hash=content_hash,
            point_id=point_id,
            start_token=start_token,
            end_token=end_token,
            has_overlap=has_overlap,
            forced_split=forced_split,
            source_metadata=source_metadata,
            structural_metadata=structural_metadata,
        )
