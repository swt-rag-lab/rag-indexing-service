"""Unit tests for PointIdPolicy."""

import uuid

import pytest

from indexing_service.domain.policies.point_id_policy import PointIdPolicy

pytestmark = pytest.mark.unit

_DOC_ID = uuid.UUID("12345678-1234-5678-1234-567812345678")
_VERSION_ID = uuid.UUID("abcdefab-cdef-abcd-efab-cdefabcdefab")


class TestPointIdPolicy:
    def test_determinism(self) -> None:
        id1 = PointIdPolicy.generate("tenant-a", _DOC_ID, _VERSION_ID, 0)
        id2 = PointIdPolicy.generate("tenant-a", _DOC_ID, _VERSION_ID, 0)
        assert id1 == id2

    def test_different_tenant_different_point_id(self) -> None:
        id1 = PointIdPolicy.generate("tenant-a", _DOC_ID, _VERSION_ID, 0)
        id2 = PointIdPolicy.generate("tenant-b", _DOC_ID, _VERSION_ID, 0)
        assert id1 != id2

    def test_different_chunk_index_different_point_id(self) -> None:
        id1 = PointIdPolicy.generate("tenant-a", _DOC_ID, _VERSION_ID, 0)
        id2 = PointIdPolicy.generate("tenant-a", _DOC_ID, _VERSION_ID, 1)
        assert id1 != id2
