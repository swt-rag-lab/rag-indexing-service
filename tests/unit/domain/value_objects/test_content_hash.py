"""Unit tests for ContentHash value object."""

import hashlib

import pytest

from indexing_service.domain.value_objects.content_hash import ContentHash

pytestmark = pytest.mark.unit


class TestContentHash:
    def test_from_text_produces_sha256(self) -> None:
        text = "hello world"
        expected = hashlib.sha256(text.encode("utf-8")).hexdigest()
        content_hash = ContentHash.from_text(text)
        assert content_hash.value == expected

    def test_same_text_same_hash(self) -> None:
        h1 = ContentHash.from_text("some content")
        h2 = ContentHash.from_text("some content")
        assert h1 == h2

    def test_different_text_different_hash(self) -> None:
        h1 = ContentHash.from_text("text A")
        h2 = ContentHash.from_text("text B")
        assert h1 != h2

    def test_hash_is_64_chars(self) -> None:
        content_hash = ContentHash.from_text("any text")
        assert len(content_hash.value) == 64

    def test_empty_value_raises(self) -> None:
        with pytest.raises(ValueError, match="must not be empty"):
            ContentHash(value="")
