"""VectorPoint — domain data structure for a point to be stored in the vector store."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class VectorPoint:
    """A point to upsert into the vector store.

    Contains the deterministic ID, the embedding vector, and the metadata payload.
    """

    id: str  # point_id (deterministic UUID string)
    vector: list[float]
    payload: dict[str, Any]
