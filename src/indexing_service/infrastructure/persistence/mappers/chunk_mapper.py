"""Mapper between Chunk domain entity and ChunkModel."""

from indexing_service.domain.entities.chunk import Chunk, SourceMetadata, StructuralMetadata
from indexing_service.domain.value_objects.chunk_id import ChunkId
from indexing_service.domain.value_objects.content_hash import ContentHash
from indexing_service.domain.value_objects.point_id import PointId
from indexing_service.domain.value_objects.tenant_id import TenantId
from indexing_service.infrastructure.persistence.models.chunk_model import ChunkModel


def to_model(entity: Chunk) -> ChunkModel:
    """Convert a Chunk domain entity to a SQLAlchemy model."""
    return ChunkModel(
        id=entity.id.value,
        tenant_id=str(entity.tenant_id),
        document_id=entity.document_id,
        version_id=entity.version_id,
        chunk_index=entity.chunk_index,
        content=entity.content,
        token_count=entity.token_count,
        start_token=entity.start_token,
        end_token=entity.end_token,
        has_overlap=entity.has_overlap,
        forced_split=entity.forced_split,
        content_hash=str(entity.content_hash),
        point_id=str(entity.point_id),
        source_content_type=entity.source_metadata.source_content_type,
        source_content_hash=entity.source_metadata.source_content_hash,
        extractor_type=entity.source_metadata.extractor_type,
        extractor_version=entity.source_metadata.extractor_version,
        embedding_model=entity.source_metadata.embedding_model,
        chunking_version=entity.source_metadata.chunking_version,
        section_type=entity.structural_metadata.section_type,
        section_title=entity.structural_metadata.section_title,
        page_start=entity.structural_metadata.page_start,
        page_end=entity.structural_metadata.page_end,
        hierarchy=entity.structural_metadata.hierarchy,
        created_at=entity.created_at,
    )


def to_entity(model: ChunkModel) -> Chunk:
    """Convert a SQLAlchemy model to a Chunk domain entity."""
    return Chunk(
        id=ChunkId(value=model.id),
        tenant_id=TenantId(value=model.tenant_id),
        document_id=model.document_id,
        version_id=model.version_id,
        chunk_index=model.chunk_index,
        content=model.content,
        token_count=model.token_count,
        start_token=model.start_token,
        end_token=model.end_token,
        has_overlap=model.has_overlap,
        forced_split=model.forced_split,
        content_hash=ContentHash(value=model.content_hash),
        point_id=PointId(value=model.point_id),
        source_metadata=SourceMetadata(
            source_content_type=model.source_content_type,
            source_content_hash=model.source_content_hash,
            extractor_type=model.extractor_type,
            extractor_version=model.extractor_version,
            embedding_model=model.embedding_model,
            chunking_version=model.chunking_version,
        ),
        structural_metadata=StructuralMetadata(
            section_type=model.section_type,
            section_title=model.section_title,
            page_start=model.page_start,
            page_end=model.page_end,
            hierarchy=model.hierarchy,
        ),
        created_at=model.created_at,
    )


def to_models(entities: list[Chunk]) -> list[ChunkModel]:
    """Convert a list of Chunk domain entities to SQLAlchemy models."""
    return [to_model(entity) for entity in entities]
