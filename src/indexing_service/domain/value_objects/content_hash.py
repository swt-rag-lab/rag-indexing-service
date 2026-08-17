"""ContentHash value object — SHA-256 hash of text content."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass


@dataclass(frozen=True)
class ContentHash:
    """SHA-256 hash of text content. Immutable, compared by value."""

    value: str

    def __post_init__(self) -> None:
        if not self.value or not self.value.strip():
            msg = "ContentHash must not be empty."
            raise ValueError(msg)
        if len(self.value) != 64:
            msg = f"ContentHash must be 64 hex chars (SHA-256), got {len(self.value)}"
            raise ValueError(msg)

    @classmethod
    def from_text(cls, text: str) -> ContentHash:
        """Compute SHA-256 hash from text content."""
        hash_hex = hashlib.sha256(text.encode("utf-8")).hexdigest()
        return cls(value=hash_hex)

    def __str__(self) -> str:
        return self.value
