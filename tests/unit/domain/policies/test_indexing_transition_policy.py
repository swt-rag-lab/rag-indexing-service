"""Unit tests for IndexingTransitionPolicy."""

import pytest

from indexing_service.domain.policies.indexing_transition_policy import (
    IndexingTransitionPolicy,
)
from indexing_service.domain.value_objects.indexing_status import IndexingStatus

pytestmark = pytest.mark.unit


class TestIndexingTransitionPolicy:
    @pytest.mark.parametrize(
        ("from_status", "to_status"),
        [
            (IndexingStatus.PENDING, IndexingStatus.CHUNKING),
            (IndexingStatus.PENDING, IndexingStatus.FAILED),
            (IndexingStatus.CHUNKING, IndexingStatus.EMBEDDING),
            (IndexingStatus.CHUNKING, IndexingStatus.FAILED),
            (IndexingStatus.EMBEDDING, IndexingStatus.STORING),
            (IndexingStatus.EMBEDDING, IndexingStatus.FAILED),
            (IndexingStatus.STORING, IndexingStatus.COMPLETED),
            (IndexingStatus.STORING, IndexingStatus.FAILED),
        ],
    )
    def test_valid_transitions(
        self, from_status: IndexingStatus, to_status: IndexingStatus
    ) -> None:
        assert IndexingTransitionPolicy.can_transition(from_status, to_status) is True

    @pytest.mark.parametrize(
        ("from_status", "to_status"),
        [
            (IndexingStatus.PENDING, IndexingStatus.EMBEDDING),
            (IndexingStatus.PENDING, IndexingStatus.STORING),
            (IndexingStatus.PENDING, IndexingStatus.COMPLETED),
            (IndexingStatus.CHUNKING, IndexingStatus.STORING),
            (IndexingStatus.CHUNKING, IndexingStatus.COMPLETED),
            (IndexingStatus.EMBEDDING, IndexingStatus.COMPLETED),
            (IndexingStatus.EMBEDDING, IndexingStatus.CHUNKING),
            (IndexingStatus.STORING, IndexingStatus.CHUNKING),
        ],
    )
    def test_invalid_transitions(
        self, from_status: IndexingStatus, to_status: IndexingStatus
    ) -> None:
        assert IndexingTransitionPolicy.can_transition(from_status, to_status) is False

    def test_completed_cannot_transition(self) -> None:
        for target in IndexingStatus:
            assert (
                IndexingTransitionPolicy.can_transition(IndexingStatus.COMPLETED, target) is False
            )

    def test_failed_cannot_transition(self) -> None:
        for target in IndexingStatus:
            assert IndexingTransitionPolicy.can_transition(IndexingStatus.FAILED, target) is False
