"""IndexingRepository port — interface for persistence of indexing data."""

from __future__ import annotations

import uuid
from typing import Protocol

from indexing_service.domain.entities.chunk import Chunk
from indexing_service.domain.entities.indexing_job import IndexingJob


class IndexingRepository(Protocol):
    """Port for persisting IndexingJobs and Chunks.

    All operations MUST be scoped to tenant_id.
    """

    async def save_job(self, job: IndexingJob) -> None:
        """Save or update an IndexingJob."""
        ...

    async def find_job_by_id(self, tenant_id: str, job_id: uuid.UUID) -> IndexingJob | None:
        """Find an IndexingJob by its ID, scoped to tenant."""
        ...

    async def find_job_by_document(
        self, tenant_id: str, document_id: uuid.UUID, version_id: uuid.UUID
    ) -> IndexingJob | None:
        """Find an IndexingJob by document and version, scoped to tenant."""
        ...

    async def save_chunks(self, chunks: list[Chunk]) -> None:
        """Bulk save chunks metadata."""
        ...

    async def delete_chunks_by_document(
        self, tenant_id: str, document_id: uuid.UUID, version_id: uuid.UUID
    ) -> int:
        """Delete all chunks for a document version. Returns count deleted."""
        ...
