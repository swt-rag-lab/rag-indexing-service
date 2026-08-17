"""IndexingJob entity — manages the lifecycle of a document indexation."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from indexing_service.domain.exceptions import InvalidStatusTransitionError
from indexing_service.domain.policies.indexing_transition_policy import IndexingTransitionPolicy
from indexing_service.domain.value_objects.indexing_status import IndexingStatus
from indexing_service.domain.value_objects.tenant_id import TenantId


class IndexingJob:
    """Entity representing the indexation lifecycle of a document version.

    Manages state transitions: PENDING → CHUNKING → EMBEDDING → STORING → COMPLETED
    Any state can transition to FAILED.
    """

    def __init__(
        self,
        id: uuid.UUID,  # noqa: A002
        tenant_id: TenantId,
        document_id: uuid.UUID,
        version_id: uuid.UUID,
        status: IndexingStatus,
        embedding_model: str,
        chunking_version: str,
        correlation_id: str,
        total_chunks: int | None = None,
        processed_chunks: int = 0,
        error_message: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> None:
        self._id = id
        self._tenant_id = tenant_id
        self._document_id = document_id
        self._version_id = version_id
        self._status = status
        self._embedding_model = embedding_model
        self._chunking_version = chunking_version
        self._correlation_id = correlation_id
        self._total_chunks = total_chunks
        self._processed_chunks = processed_chunks
        self._error_message = error_message
        self._created_at = created_at or datetime.now(UTC)
        self._updated_at = updated_at or datetime.now(UTC)

    # --- Properties ---

    @property
    def id(self) -> uuid.UUID:
        return self._id

    @property
    def tenant_id(self) -> TenantId:
        return self._tenant_id

    @property
    def document_id(self) -> uuid.UUID:
        return self._document_id

    @property
    def version_id(self) -> uuid.UUID:
        return self._version_id

    @property
    def status(self) -> IndexingStatus:
        return self._status

    @property
    def embedding_model(self) -> str:
        return self._embedding_model

    @property
    def chunking_version(self) -> str:
        return self._chunking_version

    @property
    def correlation_id(self) -> str:
        return self._correlation_id

    @property
    def total_chunks(self) -> int | None:
        return self._total_chunks

    @property
    def processed_chunks(self) -> int:
        return self._processed_chunks

    @property
    def error_message(self) -> str | None:
        return self._error_message

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    # --- State transitions ---

    def _transition_to(self, new_status: IndexingStatus) -> None:
        """Attempt a state transition. Raises if invalid."""
        if not IndexingTransitionPolicy.can_transition(self._status, new_status):
            raise InvalidStatusTransitionError(
                f"Cannot transition from {self._status} to {new_status}"
            )
        self._status = new_status
        self._updated_at = datetime.now(UTC)

    def start_chunking(self) -> None:
        """PENDING → CHUNKING."""
        self._transition_to(IndexingStatus.CHUNKING)

    def start_embedding(self, total_chunks: int) -> None:
        """CHUNKING → EMBEDDING."""
        self._transition_to(IndexingStatus.EMBEDDING)
        self._total_chunks = total_chunks

    def start_storing(self) -> None:
        """EMBEDDING → STORING."""
        self._transition_to(IndexingStatus.STORING)

    def complete(self) -> None:
        """STORING → COMPLETED."""
        if self._total_chunks is None:
            raise InvalidStatusTransitionError("Cannot complete: total_chunks has not been set.")
        self._transition_to(IndexingStatus.COMPLETED)

    def fail(self, reason: str) -> None:
        """Any state → FAILED."""
        self._status = IndexingStatus.FAILED
        self._error_message = reason
        self._updated_at = datetime.now(UTC)

    # --- Factory ---

    @classmethod
    def create(
        cls,
        *,
        tenant_id: TenantId,
        document_id: uuid.UUID,
        version_id: uuid.UUID,
        correlation_id: str,
        embedding_model: str,
        chunking_version: str,
        job_id: uuid.UUID | None = None,
    ) -> IndexingJob:
        """Create a new IndexingJob in PENDING state."""
        return cls(
            id=job_id or uuid.uuid4(),
            tenant_id=tenant_id,
            document_id=document_id,
            version_id=version_id,
            status=IndexingStatus.PENDING,
            embedding_model=embedding_model,
            chunking_version=chunking_version,
            correlation_id=correlation_id,
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, IndexingJob):
            return NotImplemented
        return self._id == other._id

    def __hash__(self) -> int:
        return hash(self._id)

    def __repr__(self) -> str:
        return f"IndexingJob(id={self._id}, status={self._status})"
