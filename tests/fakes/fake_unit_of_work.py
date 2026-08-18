"""Fake in-memory implementation of UnitOfWork for testing."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import TracebackType
from typing import Any

from tests.fakes.fake_indexing_repository import FakeIndexingRepository


@dataclass
class OutboxEvent:
    """Represents a recorded outbox event in the fake."""

    event_type: str
    payload: dict[str, Any]


class FakeUnitOfWork:
    """In-memory implementation of UnitOfWork port for testing.

    Tracks whether commit/rollback were called and stores outbox events.
    """

    def __init__(self, repository: FakeIndexingRepository | None = None) -> None:
        self.repository: FakeIndexingRepository = repository or FakeIndexingRepository()
        self.committed: bool = False
        self.rolled_back: bool = False
        self.outbox_events: list[OutboxEvent] = field(default_factory=list)
        # Re-initialize outbox_events since field() doesn't work outside dataclass
        self.outbox_events = []

    async def __aenter__(self) -> FakeUnitOfWork:
        self.committed = False
        self.rolled_back = False
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if exc_type is not None:
            self.rolled_back = True

    async def commit(self) -> None:
        """Mark the unit of work as committed."""
        self.committed = True

    async def rollback(self) -> None:
        """Mark the unit of work as rolled back."""
        self.rolled_back = True

    async def save_outbox_event(self, event_type: str, payload: dict[str, Any]) -> None:
        """Record an outbox event."""
        self.outbox_events.append(OutboxEvent(event_type=event_type, payload=payload))
