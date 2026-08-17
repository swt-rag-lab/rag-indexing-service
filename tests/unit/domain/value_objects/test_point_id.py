"""Unit tests for PointId value object."""

import uuid

import pytest

from indexing_service.domain.value_objects.point_id import PointId

pytestmark = pytest.mark.unit

_DOC_ID = uuid.UUID("12345678-1234-5678-1234-567812345678")
_VERSION_ID = uuid.UUID("abcdefab-cdef-abcd-efab-cdefabcdefab")


class TestPointId:
    def test_deterministic_generation(self) -> None:
        id1 = PointId.generate("tenant-a", _DOC_ID, _VERSION_ID, 0)
        id2 = PointId.generate("tenant-a", _DOC_ID, _VERSION_ID, 0)
        assert id1 == id2

    def test_different_inputs_different_ids(self) -> None:
        id1 = PointId.generate("tenant-a", _DOC_ID, _VERSION_ID, 0)
        id2 = PointId.generate("tenant-a", _DOC_ID, _VERSION_ID, 1)
        assert id1 != id2

    def test_includes_tenant_in_computation(self) -> None:
        id1 = PointId.generate("tenant-a", _DOC_ID, _VERSION_ID, 0)
        id2 = PointId.generate("tenant-b", _DOC_ID, _VERSION_ID, 0)
        assert id1 != id2
