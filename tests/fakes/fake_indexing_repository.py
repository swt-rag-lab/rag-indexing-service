"""Fake in-memory implementation of IndexingRepository for testing."""

import uuid

from indexing_service.domain.entities.chunk import Chunk
from indexing_service.domain.entities.indexing_job import IndexingJob


class FakeIndexingRepository:
    """In-memory implementation of IndexingRepository port.

    Stores data in dictionaries, filters by tenant_id.
    """

    def __init__(self) -> None:
        self.jobs: dict[uuid.UUID, IndexingJob] = {}
        self.chunks: list[Chunk] = []

    async def save_job(self, job: IndexingJob) -> None:
        """Save or update an IndexingJob."""
        self.jobs[job.id] = job

    async def find_job_by_id(self, tenant_id: str, job_id: uuid.UUID) -> IndexingJob | None:
        """Find an IndexingJob by ID, scoped to tenant."""
        job = self.jobs.get(job_id)
        if job is not None and str(job.tenant_id) == tenant_id:
            return job
        return None

    async def find_job_by_document(
        self, tenant_id: str, document_id: uuid.UUID, version_id: uuid.UUID
    ) -> IndexingJob | None:
        """Find an IndexingJob by document and version, scoped to tenant."""
        for job in self.jobs.values():
            if (
                str(job.tenant_id) == tenant_id
                and job.document_id == document_id
                and job.version_id == version_id
            ):
                return job
        return None

    async def save_chunks(self, chunks: list[Chunk]) -> None:
        """Bulk save chunk metadata."""
        self.chunks.extend(chunks)

    async def delete_chunks_by_document(
        self, tenant_id: str, document_id: uuid.UUID, version_id: uuid.UUID
    ) -> int:
        """Delete all chunks for a document version. Returns count deleted."""
        to_delete = [
            c
            for c in self.chunks
            if str(c.tenant_id) == tenant_id
            and c.document_id == document_id
            and c.version_id == version_id
        ]
        for chunk in to_delete:
            self.chunks.remove(chunk)
        return len(to_delete)
