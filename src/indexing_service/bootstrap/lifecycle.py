"""Application lifecycle management - startup and shutdown."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from indexing_service.bootstrap.container import get_container, init_container
from indexing_service.config.settings import Settings
from indexing_service.infrastructure.observability.logging import configure_logging, get_logger


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler.

    Startup:
    - Initialize container with settings
    - Configure logging
    - Verify infrastructure connections

    Shutdown:
    - Dispose of all resources
    """
    settings = Settings()

    configure_logging(
        log_level=settings.log_level,
        log_format=settings.log_format,
        service_name=settings.service_name,
    )

    logger = get_logger(__name__)

    container = init_container(settings)

    await logger.ainfo(
        "application_starting",
        app_name=settings.app_name,
        app_version=settings.app_version,
        app_env=settings.app_env,
    )

    # Verify connections at startup
    postgres_ok = await container.check_postgres()
    rabbitmq_ok = await container.check_rabbitmq()
    qdrant_ok = container.check_qdrant()

    await logger.ainfo(
        "infrastructure_checks",
        postgres=postgres_ok,
        rabbitmq=rabbitmq_ok,
        qdrant=qdrant_ok,
    )

    if not all([postgres_ok, rabbitmq_ok, qdrant_ok]):
        await logger.awarning(
            "infrastructure_degraded",
            postgres=postgres_ok,
            rabbitmq=rabbitmq_ok,
            qdrant=qdrant_ok,
        )

    yield

    # Shutdown
    await logger.ainfo("application_shutting_down")
    container = get_container()
    await container.close()
    await logger.ainfo("application_stopped")
