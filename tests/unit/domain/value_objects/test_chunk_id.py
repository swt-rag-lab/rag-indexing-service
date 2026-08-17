"""Unit tests for ChunkId value object."""

import uuid

import pytest

from indexing_service.domain.value_objects.chunk_id import ChunkId

pytestmark = pytest.mark.unit

_DOC_ID = uuid.UUID("12345678-1234-5678-1234-567812345678")
_VERSION_ID = uuid.UUID("abcdefab-cdef-abcd-efab-cdefabcdefab")


class TestChunkId:
    def test_deterministic_generation(self) -> None:
        id1 = ChunkId.generate(_DOC_ID, _VERSION_ID, 0)
        id2 = ChunkId.generate(_DOC_ID, _VERSION_ID, 0)
        assert id1 == id2

    def test_different_inputs_different_ids(self) -> None:
        id1 = ChunkId.generate(_DOC_ID, _VERSION_ID, 0)
        id2 = ChunkId.generate(_DOC_ID, _VERSION_ID, 1)
        assert id1 != id2

    def test_str_returns_uuid_string(self) -> None:
        chunk_id = ChunkId.generate(_DOC_ID, _VERSION_ID, 0)
        result = str(chunk_id)
        # Should be a valid UUID string
        parsed = uuid.UUID(result)
        assert str(parsed) == result
