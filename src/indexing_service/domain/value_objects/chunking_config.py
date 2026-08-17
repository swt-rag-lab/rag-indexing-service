"""ChunkingConfig value object."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ChunkingConfig:
    """Configuration for the chunking strategy."""

    max_tokens: int = 1024
    overlap_tokens: int = 200
    version: str = "semantic-v1"

    def __post_init__(self) -> None:
        if self.max_tokens <= 0:
            msg = f"max_tokens must be > 0, got {self.max_tokens}"
            raise ValueError(msg)
        if self.overlap_tokens < 0:
            msg = f"overlap_tokens must be >= 0, got {self.overlap_tokens}"
            raise ValueError(msg)
        if self.overlap_tokens >= self.max_tokens:
            msg = (
                f"overlap_tokens ({self.overlap_tokens}) must be < "
                f"max_tokens ({self.max_tokens})"
            )
            raise ValueError(msg)
        if not self.version or not self.version.strip():
            msg = "ChunkingConfig version must not be empty."
            raise ValueError(msg)
