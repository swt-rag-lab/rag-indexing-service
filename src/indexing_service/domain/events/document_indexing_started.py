"""DocumentIndexingStarted domain event."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True)
class DocumentIndexingStarted:
    """Emitted when document indexing begins."""

    tenant_id: str
    document_id: uuid.UUID
    version_id: uuid.UUID
    job_id: uuid.UUID
    correlation_id: str
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    schema_version: str = "1"

    @property
    def event_type(self) -> str:
        return "document.indexing.started.v1"
