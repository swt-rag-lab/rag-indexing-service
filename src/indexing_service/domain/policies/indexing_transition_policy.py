"""IndexingTransitionPolicy — defines valid state transitions for IndexingJob."""

from __future__ import annotations

from indexing_service.domain.value_objects.indexing_status import IndexingStatus

# Valid transitions: {from_status: [allowed_targets]}
_VALID_TRANSITIONS: dict[IndexingStatus, list[IndexingStatus]] = {
    IndexingStatus.PENDING: [IndexingStatus.CHUNKING, IndexingStatus.FAILED],
    IndexingStatus.CHUNKING: [IndexingStatus.EMBEDDING, IndexingStatus.FAILED],
    IndexingStatus.EMBEDDING: [IndexingStatus.STORING, IndexingStatus.FAILED],
    IndexingStatus.STORING: [IndexingStatus.COMPLETED, IndexingStatus.FAILED],
    IndexingStatus.COMPLETED: [],
    IndexingStatus.FAILED: [],
}


class IndexingTransitionPolicy:
    """Policy that defines valid state transitions for IndexingJob.

    PENDING → CHUNKING → EMBEDDING → STORING → COMPLETED
    Any state (except COMPLETED/FAILED) → FAILED
    """

    @staticmethod
    def can_transition(from_status: IndexingStatus, to_status: IndexingStatus) -> bool:
        """Check if a transition is valid.

        Args:
            from_status: Current status.
            to_status: Desired target status.

        Returns:
            True if the transition is allowed.
        """
        allowed = _VALID_TRANSITIONS.get(from_status, [])
        return to_status in allowed
