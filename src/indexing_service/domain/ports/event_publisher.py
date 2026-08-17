"""EventPublisher port — interface for publishing domain events."""

from __future__ import annotations

from typing import Any, Protocol


class EventPublisher(Protocol):
    """Port for publishing events to a message broker.

    Used by the outbox publisher to send events to RabbitMQ.
    """

    async def publish(self, event_type: str, payload: dict[str, Any]) -> None:
        """Publish an event.

        Args:
            event_type: Routing key / event type string.
            payload: Serialized event payload.
        """
        ...
