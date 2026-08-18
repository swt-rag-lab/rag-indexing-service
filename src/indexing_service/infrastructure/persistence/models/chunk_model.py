"""SQLAlchemy model for chunks table."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from indexing_service.infrastructure.persistence.models.base import Base


class ChunkModel(Base):
    """Mapped table: chunks."""

    __tablename__ = "chunks"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(100), nullable=False)
    document_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    version_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False)
    start_token: Mapped[int] = mapped_column(Integer, nullable=False)
    end_token: Mapped[int] = mapped_column(Integer, nullable=False)
    has_overlap: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    forced_split: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    point_id: Mapped[str] = mapped_column(String(36), nullable=False)
    source_content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    source_content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    extractor_type: Mapped[str] = mapped_column(String(50), nullable=False)
    extractor_version: Mapped[str] = mapped_column(String(20), nullable=False)
    embedding_model: Mapped[str] = mapped_column(String(100), nullable=False)
    chunking_version: Mapped[str] = mapped_column(String(50), nullable=False)
    section_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    section_title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    page_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hierarchy: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    __table_args__ = (
        Index("ix_chunks_tenant_document", "tenant_id", "document_id", "version_id"),
        Index("ix_chunks_point_id", "point_id", unique=True),
        Index("ix_chunks_section_type", "tenant_id", "section_type"),
    )
