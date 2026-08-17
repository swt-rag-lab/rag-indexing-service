"""Unit tests for ChunkingConfig value object."""

import pytest

from indexing_service.domain.value_objects.chunking_config import ChunkingConfig

pytestmark = pytest.mark.unit


class TestChunkingConfig:
    def test_valid_creation_with_defaults(self) -> None:
        config = ChunkingConfig()
        assert config.max_tokens == 1024
        assert config.overlap_tokens == 200
        assert config.version == "semantic-v1"

    def test_overlap_gte_max_raises(self) -> None:
        with pytest.raises(ValueError, match="overlap_tokens.*must be <.*max_tokens"):
            ChunkingConfig(max_tokens=100, overlap_tokens=100)

    def test_zero_max_tokens_raises(self) -> None:
        with pytest.raises(ValueError, match="max_tokens must be > 0"):
            ChunkingConfig(max_tokens=0)
