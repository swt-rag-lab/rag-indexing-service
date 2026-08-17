"""Dependency container - composition root for the application."""

from dataclasses import dataclass, field
from typing import Any

import aio_pika
from qdrant_client import QdrantClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from indexing_service.config.settings import Settings


@dataclass
class Container:
    """Application dependency container.

    Holds references to shared infrastructure resources like database engines,
    message broker connections, and vector store clients.
    """

    settings: Settings
    db_engine: AsyncEngine = field(init=False)
    qdrant_client: QdrantClient = field(init=False)
    health_check_query: Any = field(default_factory=lambda: text("SELECT 1"))

    def __post_init__(self) -> None:
        self.db_engine = create_async_engine(
            self.settings.database_url,
            echo=False,
            pool_pre_ping=True,
        )
        self.qdrant_client = QdrantClient(
            host=self.settings.qdrant_host,
            port=self.settings.qdrant_port,
            api_key=self.settings.qdrant_api_key or None,
        )

    async def check_postgres(self) -> bool:
        """Check PostgreSQL connectivity."""
        try:
            async with self.db_engine.connect() as conn:
                await conn.execute(self.health_check_query)
            return True
        except Exception:
            return False

    async def check_rabbitmq(self) -> bool:
        """Check RabbitMQ connectivity."""
        try:
            connection = await aio_pika.connect_robust(self.settings.rabbitmq_url)
            await connection.close()
            return True
        except Exception:
            return False

    def check_qdrant(self) -> bool:
        """Check Qdrant connectivity."""
        try:
            self.qdrant_client.get_collections()
            return True
        except Exception:
            return False

    async def close(self) -> None:
        """Dispose of all resources."""
        await self.db_engine.dispose()
        self.qdrant_client.close()


_container: Container | None = None


def init_container(settings: Settings) -> Container:
    """Initialize the global container."""
    global _container  # noqa: PLW0603
    _container = Container(settings=settings)
    return _container


def get_container() -> Container:
    """Get the global container. Raises if not initialized."""
    if _container is None:
        msg = "Container not initialized. Call init_container() first."
        raise RuntimeError(msg)
    return _container
