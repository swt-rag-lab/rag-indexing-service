"""Unit tests for Chunk entity."""

import uuid

import pytest

from indexing_service.domain.entities.chunk import Chunk, SourceMetadata, StructuralMetadata
from indexing_service.domain.value_objects.content_hash import ContentHash
from indexing_service.domain.value_objects.tenant_id import TenantId

pytestmark = pytest.mark.unit

_TENANT = TenantId(value="tenant-1")
_DOC_ID = uuid.UUID("12345678-1234-5678-1234-567812345678")
_VERSION_ID = uuid.UUID("abcdefab-cdef-abcd-efab-cdefabcdefab")

_SOURCE_META = SourceMetadata(
    source_content_type="application/pdf",
    source_content_hash="abc123",
    extractor_type="docling",
    extractor_version="1.0",
    embedding_model="text-embedding-3-small",
    chunking_version="semantic-v1",
)

_STRUCTURAL_META = StructuralMetadata(
    section_type="paragraph",
    section_title="Introduction",
)


def _create_chunk(**overrides: object) -> Chunk:
    defaults: dict[str, object] = {
        "tenant_id": _TENANT,
        "document_id": _DOC_ID,
        "version_id": _VERSION_ID,
        "chunk_index": 0,
        "content": "This is chunk content.",
        "token_count": 5,
        "start_token": 0,
        "end_token": 5,
        "has_overlap": False,
        "forced_split": False,
        "source_metadata": _SOURCE_META,
        "structural_metadata": _STRUCTURAL_META,
    }
    defaults.update(overrides)
    return Chunk.create(**defaults)  # type: ignore[arg-type]


class TestChunk:
    def test_create_with_factory_method(self) -> None:
        chunk = _create_chunk()
        assert chunk.content == "This is chunk content."
        assert chunk.tenant_id == _TENANT
        assert chunk.chunk_index == 0

    def test_deterministic_ids(self) -> None:
        c1 = _create_chunk()
        c2 = _create_chunk()
        assert c1.id == c2.id
        assert c1.point_id == c2.point_id

    def test_content_hash_computed(self) -> None:
        chunk = _create_chunk()
        expected = ContentHash.from_text("This is chunk content.")
        assert chunk.content_hash == expected

    def test_empty_content_raises(self) -> None:
        with pytest.raises(ValueError, match="content must not be empty"):
            _create_chunk(content="")

    def test_zero_token_count_raises(self) -> None:
        with pytest.raises(ValueError, match="token_count must be > 0"):
            _create_chunk(token_count=0)

    def test_negative_chunk_index_raises(self) -> None:
        with pytest.raises(ValueError, match="chunk_index must be >= 0"):
            _create_chunk(chunk_index=-1)

    def test_end_token_lte_start_token_raises(self) -> None:
        with pytest.raises(ValueError, match="end_token.*must be > start_token"):
            _create_chunk(start_token=5, end_token=5)
