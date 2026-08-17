"""UnitOfWork port — interface for transactional boundaries."""

from __future__ import annotations

from typing import Any, Protocol


class UnitOfWork(Protocol):
    """Port for managing transactional boundaries.

    Ensures that domain state changes and outbox events are committed atomically.
    """

    async def commit(self) -> None:
        """Commit the current transaction."""
        ...

    async def rollback(self) -> None:
        """Rollback the current transaction."""
        ...

    async def save_outbox_event(self, event_type: str, payload: dict[str, Any]) -> None:
        """Save a domain event to the outbox within the current transaction.

        Args:
            event_type: The event type/routing key (e.g. 'document.indexed.v1').
            payload: Serialized event payload as a dictionary.
        """
        ...
