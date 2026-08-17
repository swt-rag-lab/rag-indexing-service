"""EmbeddingModel value object."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EmbeddingModel:
    """Describes an embedding model configuration."""

    name: str
    dimensions: int
    version: str

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            msg = "EmbeddingModel name must not be empty."
            raise ValueError(msg)
        if self.dimensions <= 0:
            msg = f"EmbeddingModel dimensions must be > 0, got {self.dimensions}"
            raise ValueError(msg)
        if not self.version or not self.version.strip():
            msg = "EmbeddingModel version must not be empty."
            raise ValueError(msg)
