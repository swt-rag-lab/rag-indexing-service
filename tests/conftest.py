"""Shared test fixtures."""

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from indexing_service.bootstrap.container import Container
from indexing_service.config.settings import Settings
from indexing_service.main import create_app


@pytest.fixture
def test_settings() -> Settings:
    """Create test settings with safe defaults."""
    return Settings(
        app_env="test",
        database_url="postgresql+asyncpg://postgres:postgres@localhost:5432/indexing_test",
        qdrant_host="localhost",
        qdrant_port=6333,
        openai_api_key="sk-test-key",
        rabbitmq_url="amqp://rabbitmq:rabbitmq@localhost:5672/rag-lab",
    )


@pytest.fixture
def mock_container(test_settings: Settings) -> Container:
    """Create a container with mocked infrastructure checks."""
    with (
        patch.object(Container, "__post_init__"),
    ):
        container = Container(settings=test_settings)
        container.db_engine = MagicMock()  # type: ignore[assignment]
        container.qdrant_client = MagicMock()
        container.check_postgres = AsyncMock(return_value=True)  # type: ignore[method-assign]
        container.check_rabbitmq = AsyncMock(return_value=True)  # type: ignore[method-assign]
        container.check_qdrant = MagicMock(return_value=True)  # type: ignore[method-assign]
        container.close = AsyncMock()  # type: ignore[method-assign]
        return container


@pytest.fixture
async def async_client(mock_container: Container) -> AsyncGenerator[AsyncClient, None]:
    """Create an HTTPX async client for testing."""
    with (
        patch(
            "indexing_service.bootstrap.lifecycle.init_container",
            return_value=mock_container,
        ),
        patch(
            "indexing_service.bootstrap.lifecycle.get_container",
            return_value=mock_container,
        ),
        patch(
            "indexing_service.api.routes.health.get_container",
            return_value=mock_container,
        ),
    ):
        app = create_app()
        transport = ASGITransport(app=app)  # type: ignore[arg-type]
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client
