"""ChunkingStrategy port — interface for text chunking."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class ChunkResult:
    """Result of chunking a single piece of text."""

    content: str
    token_count: int
    index: int
    start_token: int
    end_token: int
    has_overlap: bool
    forced_split: bool
    section_type: str | None = None
    section_title: str | None = None
    page_start: int | None = None
    page_end: int | None = None
    hierarchy: list[str] = field(default_factory=list)


class ChunkingStrategy(Protocol):
    """Port for splitting text into chunks.

    Implementations may use semantic chunking, fixed-size, etc.
    The domain does not know which strategy is used.
    """

    def chunk(self, text: str) -> list[ChunkResult]:
        """Split text into chunks with structural metadata.

        Args:
            text: The full canonical text (Markdown) to chunk.

        Returns:
            Ordered list of ChunkResults with metadata.
        """
        ...
