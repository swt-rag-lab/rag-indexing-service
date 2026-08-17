"""IndexingStatus value object — lifecycle states for an IndexingJob."""

from __future__ import annotations

from enum import StrEnum


class IndexingStatus(StrEnum):
    """Lifecycle states for an IndexingJob."""

    PENDING = "PENDING"
    CHUNKING = "CHUNKING"
    EMBEDDING = "EMBEDDING"
    STORING = "STORING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
