"""SQLAlchemy implementation of the IndexingRepository port."""

import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from indexing_service.domain.entities.chunk import Chunk
from indexing_service.domain.entities.indexing_job import IndexingJob
from indexing_service.infrastructure.persistence.mappers import chunk_mapper, indexing_job_mapper
from indexing_service.infrastructure.persistence.models.chunk_model import ChunkModel
from indexing_service.infrastructure.persistence.models.indexing_job_model import IndexingJobModel


class SqlAlchemyIndexingRepository:
    """Implements IndexingRepository port using SQLAlchemy async sessions.

    All queries are scoped to tenant_id for multi-tenancy isolation.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save_job(self, job: IndexingJob) -> None:
        """Save or update an IndexingJob (upsert via merge)."""
        model = indexing_job_mapper.to_model(job)
        await self._session.merge(model)

    async def find_job_by_id(self, tenant_id: str, job_id: uuid.UUID) -> IndexingJob | None:
        """Find an IndexingJob by ID, scoped to tenant."""
        stmt = select(IndexingJobModel).where(
            IndexingJobModel.tenant_id == tenant_id,
            IndexingJobModel.id == job_id,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return indexing_job_mapper.to_entity(model)

    async def find_job_by_document(
        self, tenant_id: str, document_id: uuid.UUID, version_id: uuid.UUID
    ) -> IndexingJob | None:
        """Find an IndexingJob by document and version, scoped to tenant."""
        stmt = select(IndexingJobModel).where(
            IndexingJobModel.tenant_id == tenant_id,
            IndexingJobModel.document_id == document_id,
            IndexingJobModel.version_id == version_id,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return indexing_job_mapper.to_entity(model)

    async def save_chunks(self, chunks: list[Chunk]) -> None:
        """Bulk save chunk metadata."""
        models = chunk_mapper.to_models(chunks)
        self._session.add_all(models)

    async def delete_chunks_by_document(
        self, tenant_id: str, document_id: uuid.UUID, version_id: uuid.UUID
    ) -> int:
        """Delete all chunks for a document version. Returns count deleted."""
        stmt = (
            delete(ChunkModel)
            .where(
                ChunkModel.tenant_id == tenant_id,
                ChunkModel.document_id == document_id,
                ChunkModel.version_id == version_id,
            )
            .returning(ChunkModel.id)
        )
        result = await self._session.execute(stmt)
        return len(result.all())
