"""Embedder port — interface for embedding generation."""

from __future__ import annotations

from typing import Protocol


class Embedder(Protocol):
    """Port for generating text embeddings.

    Implementations may use OpenAI, Cohere, local models, etc.
    The domain does not know which provider is used.
    """

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of texts.

        Args:
            texts: List of text strings to embed.

        Returns:
            List of embedding vectors. results[i] corresponds to texts[i].
        """
        ...

    @property
    def model_name(self) -> str:
        """Name of the embedding model."""
        ...

    @property
    def dimensions(self) -> int:
        """Dimensionality of the embedding vectors."""
        ...
