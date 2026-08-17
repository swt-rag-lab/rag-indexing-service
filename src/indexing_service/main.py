"""Application entry point - FastAPI app factory."""

from fastapi import FastAPI

from indexing_service.api.middleware import RequestTraceMiddleware
from indexing_service.api.routes.health import router as health_router
from indexing_service.bootstrap.lifecycle import lifespan


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance.
    """
    app = FastAPI(
        title="Indexing Service",
        description="RAG Lab - Document indexing service",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Middleware
    app.add_middleware(RequestTraceMiddleware)

    # Routes
    app.include_router(health_router)

    return app
