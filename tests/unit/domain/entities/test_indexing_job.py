"""Unit tests for IndexingJob entity."""

import uuid

import pytest

from indexing_service.domain.entities.indexing_job import IndexingJob
from indexing_service.domain.exceptions import InvalidStatusTransitionError
from indexing_service.domain.value_objects.indexing_status import IndexingStatus
from indexing_service.domain.value_objects.tenant_id import TenantId

pytestmark = pytest.mark.unit

_TENANT = TenantId(value="tenant-1")
_DOC_ID = uuid.UUID("12345678-1234-5678-1234-567812345678")
_VERSION_ID = uuid.UUID("abcdefab-cdef-abcd-efab-cdefabcdefab")


def _create_job() -> IndexingJob:
    return IndexingJob.create(
        tenant_id=_TENANT,
        document_id=_DOC_ID,
        version_id=_VERSION_ID,
        correlation_id="corr-123",
        embedding_model="text-embedding-3-small",
        chunking_version="semantic-v1",
    )


class TestIndexingJob:
    def test_create_in_pending_state(self) -> None:
        job = _create_job()
        assert job.status == IndexingStatus.PENDING

    def test_start_chunking_from_pending(self) -> None:
        job = _create_job()
        job.start_chunking()
        assert job.status == IndexingStatus.CHUNKING

    def test_start_embedding_from_chunking(self) -> None:
        job = _create_job()
        job.start_chunking()
        job.start_embedding(total_chunks=10)
        assert job.status == IndexingStatus.EMBEDDING

    def test_start_storing_from_embedding(self) -> None:
        job = _create_job()
        job.start_chunking()
        job.start_embedding(total_chunks=10)
        job.start_storing()
        assert job.status == IndexingStatus.STORING

    def test_complete_from_storing(self) -> None:
        job = _create_job()
        job.start_chunking()
        job.start_embedding(total_chunks=10)
        job.start_storing()
        job.complete()
        assert job.status == IndexingStatus.COMPLETED

    @pytest.mark.parametrize(
        "initial_status",
        [
            IndexingStatus.PENDING,
            IndexingStatus.CHUNKING,
            IndexingStatus.EMBEDDING,
            IndexingStatus.STORING,
        ],
    )
    def test_fail_from_any_state(self, initial_status: IndexingStatus) -> None:
        job = _create_job()
        # Advance to the desired state
        if initial_status in (
            IndexingStatus.CHUNKING,
            IndexingStatus.EMBEDDING,
            IndexingStatus.STORING,
        ):
            job.start_chunking()
        if initial_status in (IndexingStatus.EMBEDDING, IndexingStatus.STORING):
            job.start_embedding(total_chunks=5)
        if initial_status == IndexingStatus.STORING:
            job.start_storing()

        job.fail("something went wrong")
        assert job.status == IndexingStatus.FAILED
        assert job.error_message == "something went wrong"

    def test_invalid_transition_pending_to_storing_raises(self) -> None:
        job = _create_job()
        with pytest.raises(InvalidStatusTransitionError):
            job.start_storing()

    def test_invalid_transition_pending_to_completed_raises(self) -> None:
        job = _create_job()
        with pytest.raises(InvalidStatusTransitionError):
            job.complete()

    def test_complete_without_total_chunks_raises(self) -> None:
        job = _create_job()
        job.start_chunking()
        # Manually force to STORING without setting total_chunks through start_embedding
        job._status = IndexingStatus.STORING
        with pytest.raises(InvalidStatusTransitionError, match="total_chunks"):
            job.complete()

    def test_start_embedding_sets_total_chunks(self) -> None:
        job = _create_job()
        job.start_chunking()
        job.start_embedding(total_chunks=42)
        assert job.total_chunks == 42
