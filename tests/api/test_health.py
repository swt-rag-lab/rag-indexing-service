"""Tests for health check endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

from indexing_service.bootstrap.container import Container

pytestmark = pytest.mark.api


async def test_liveness_returns_200(async_client: AsyncClient) -> None:
    """GET /health/live should return 200 with status alive."""
    response = await async_client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


async def test_readiness_all_healthy(async_client: AsyncClient) -> None:
    """GET /health/ready should return 200 when all services are healthy."""
    response = await async_client.get("/health/ready")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["checks"]["postgres"] == "ok"
    assert data["checks"]["rabbitmq"] == "ok"
    assert data["checks"]["qdrant"] == "ok"


async def test_readiness_postgres_down(
    async_client: AsyncClient, mock_container: Container
) -> None:
    """GET /health/ready should return 503 when PostgreSQL is down."""
    mock_container.check_postgres = AsyncMock(return_value=False)  # type: ignore[method-assign]

    with patch(
        "indexing_service.api.routes.health.get_container",
        return_value=mock_container,
    ):
        response = await async_client.get("/health/ready")

    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "degraded"
    assert data["checks"]["postgres"] == "failed"


async def test_readiness_qdrant_down(async_client: AsyncClient, mock_container: Container) -> None:
    """GET /health/ready should return 503 when Qdrant is down."""
    mock_container.check_qdrant = MagicMock(return_value=False)  # type: ignore[method-assign]

    with patch(
        "indexing_service.api.routes.health.get_container",
        return_value=mock_container,
    ):
        response = await async_client.get("/health/ready")

    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "degraded"
    assert data["checks"]["qdrant"] == "failed"


async def test_readiness_rabbitmq_down(
    async_client: AsyncClient, mock_container: Container
) -> None:
    """GET /health/ready should return 503 when RabbitMQ is down."""
    mock_container.check_rabbitmq = AsyncMock(return_value=False)  # type: ignore[method-assign]

    with patch(
        "indexing_service.api.routes.health.get_container",
        return_value=mock_container,
    ):
        response = await async_client.get("/health/ready")

    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "degraded"
    assert data["checks"]["rabbitmq"] == "failed"


async def test_liveness_has_request_id_header(async_client: AsyncClient) -> None:
    """Responses should include X-Request-ID header from middleware."""
    response = await async_client.get("/health/live")

    assert "x-request-id" in response.headers
    assert "x-correlation-id" in response.headers
