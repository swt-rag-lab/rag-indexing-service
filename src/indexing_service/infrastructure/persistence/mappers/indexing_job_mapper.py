"""Mapper between IndexingJob domain entity and IndexingJobModel."""

from indexing_service.domain.entities.indexing_job import IndexingJob
from indexing_service.domain.value_objects.indexing_status import IndexingStatus
from indexing_service.domain.value_objects.tenant_id import TenantId
from indexing_service.infrastructure.persistence.models.indexing_job_model import IndexingJobModel


def to_model(entity: IndexingJob) -> IndexingJobModel:
    """Convert an IndexingJob domain entity to a SQLAlchemy model."""
    return IndexingJobModel(
        id=entity.id,
        tenant_id=str(entity.tenant_id),
        document_id=entity.document_id,
        version_id=entity.version_id,
        status=entity.status.value,
        total_chunks=entity.total_chunks,
        processed_chunks=entity.processed_chunks,
        embedding_model=entity.embedding_model,
        chunking_version=entity.chunking_version,
        error_message=entity.error_message,
        correlation_id=entity.correlation_id,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


def to_entity(model: IndexingJobModel) -> IndexingJob:
    """Convert a SQLAlchemy model to an IndexingJob domain entity."""
    return IndexingJob(
        id=model.id,
        tenant_id=TenantId(value=model.tenant_id),
        document_id=model.document_id,
        version_id=model.version_id,
        status=IndexingStatus(model.status),
        total_chunks=model.total_chunks,
        processed_chunks=model.processed_chunks,
        embedding_model=model.embedding_model,
        chunking_version=model.chunking_version,
        error_message=model.error_message,
        correlation_id=model.correlation_id,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )
