"""CanonicalReader port — interface for reading canonical text from storage."""

from __future__ import annotations

from typing import Protocol


class CanonicalReader(Protocol):
    """Port for reading canonical document text.

    Implementations may use MinIO, S3, local filesystem, etc.
    """

    async def read_canonical(self, location: str) -> str:
        """Read the canonical text from storage.

        Args:
            location: Object key / path to the canonical text.

        Returns:
            The canonical text content (UTF-8).

        Raises:
            CanonicalReadError: If the read fails.
        """
        ...
