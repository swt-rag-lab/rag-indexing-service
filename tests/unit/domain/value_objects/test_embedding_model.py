"""Unit tests for EmbeddingModel value object."""

import pytest

from indexing_service.domain.value_objects.embedding_model import EmbeddingModel

pytestmark = pytest.mark.unit


class TestEmbeddingModel:
    def test_valid_creation(self) -> None:
        model = EmbeddingModel(name="text-embedding-3-small", dimensions=1536, version="v1")
        assert model.name == "text-embedding-3-small"
        assert model.dimensions == 1536
        assert model.version == "v1"

    def test_empty_name_raises(self) -> None:
        with pytest.raises(ValueError, match="name must not be empty"):
            EmbeddingModel(name="", dimensions=1536, version="v1")

    def test_zero_dimensions_raises(self) -> None:
        with pytest.raises(ValueError, match="dimensions must be > 0"):
            EmbeddingModel(name="text-embedding-3-small", dimensions=0, version="v1")

    def test_negative_dimensions_raises(self) -> None:
        with pytest.raises(ValueError, match="dimensions must be > 0"):
            EmbeddingModel(name="text-embedding-3-small", dimensions=-1, version="v1")
