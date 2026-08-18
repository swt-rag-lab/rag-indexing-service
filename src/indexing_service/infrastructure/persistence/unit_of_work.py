"""SQLAlchemy implementation of the UnitOfWork port."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from types import TracebackType
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from indexing_service.infrastructure.persistence.models.outbox_event_model import OutboxEventModel
from indexing_service.infrastructure.persistence.repositories.sqlalchemy_indexing_repository import (
    SqlAlchemyIndexingRepository,
)


class SqlAlchemyUnitOfWork:
    """Manages transactional boundaries using SQLAlchemy async sessions.

    Usage:
        async with uow:
            await uow.repository.save_job(job)
            await uow.save_outbox_event("document.indexed.v1", payload)
            await uow.commit()
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory
        self._session: AsyncSession | None = None
        self._repository: SqlAlchemyIndexingRepository | None = None

    @property
    def repository(self) -> SqlAlchemyIndexingRepository:
        """Access the repository for the current session."""
        if self._repository is None:
            msg = "UnitOfWork has not been entered. Use 'async with uow:'"
            raise RuntimeError(msg)
        return self._repository

    async def __aenter__(self) -> SqlAlchemyUnitOfWork:
        self._session = self._session_factory()
        self._repository = SqlAlchemyIndexingRepository(self._session)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if self._session:
            if exc_type is not None:
                await self._session.rollback()
            await self._session.close()
            self._session = None
            self._repository = None

    async def commit(self) -> None:
        """Commit the current transaction."""
        if self._session is None:
            msg = "UnitOfWork has not been entered. Use 'async with uow:'"
            raise RuntimeError(msg)
        await self._session.commit()

    async def rollback(self) -> None:
        """Rollback the current transaction."""
        if self._session is None:
            msg = "UnitOfWork has not been entered. Use 'async with uow:'"
            raise RuntimeError(msg)
        await self._session.rollback()

    async def save_outbox_event(self, event_type: str, payload: dict[str, Any]) -> None:
        """Save a domain event to the outbox within the current transaction."""
        if self._session is None:
            msg = "UnitOfWork has not been entered. Use 'async with uow:'"
            raise RuntimeError(msg)
        event = OutboxEventModel(
            id=uuid.uuid4(),
            event_type=event_type,
            payload=payload,
            status="pending",
            attempts=0,
            max_attempts=5,
            created_at=datetime.now(UTC),
        )
        self._session.add(event)
