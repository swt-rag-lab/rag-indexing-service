"""Unit tests for IndexingStatus value object."""

from enum import StrEnum

import pytest

from indexing_service.domain.value_objects.indexing_status import IndexingStatus

pytestmark = pytest.mark.unit


class TestIndexingStatus:
    def test_all_status_values_exist(self) -> None:
        expected = {"PENDING", "CHUNKING", "EMBEDDING", "STORING", "COMPLETED", "FAILED"}
        actual = {s.value for s in IndexingStatus}
        assert actual == expected

    def test_status_is_string_enum(self) -> None:
        assert issubclass(IndexingStatus, StrEnum)
        assert IndexingStatus.PENDING == "PENDING"
        assert isinstance(IndexingStatus.CHUNKING, str)
