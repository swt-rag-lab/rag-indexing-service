"""DocumentIndexed domain event."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True)
class DocumentIndexed:
    """Emitted when document indexing completes successfully."""

    tenant_id: str
    document_id: uuid.UUID
    version_id: uuid.UUID
    job_id: uuid.UUID
    total_chunks: int
    embedding_model: str
    chunking_version: str
    correlation_id: str
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    schema_version: str = "1"

    @property
    def event_type(self) -> str:
        return "document.indexed.v1"
