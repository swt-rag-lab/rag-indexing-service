"""Health check endpoints."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from starlette.responses import Response

from indexing_service.bootstrap.container import get_container

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
async def liveness() -> dict[str, str]:
    """Liveness probe - returns 200 if the process is running."""
    return {"status": "alive"}


@router.get("/ready", status_code=200)
async def readiness() -> Response:
    """Readiness probe - verifies PostgreSQL, RabbitMQ, and Qdrant connectivity."""
    container = get_container()

    postgres_ok = await container.check_postgres()
    rabbitmq_ok = await container.check_rabbitmq()
    qdrant_ok = container.check_qdrant()

    checks = {
        "postgres": "ok" if postgres_ok else "failed",
        "rabbitmq": "ok" if rabbitmq_ok else "failed",
        "qdrant": "ok" if qdrant_ok else "failed",
    }

    all_healthy = all([postgres_ok, rabbitmq_ok, qdrant_ok])

    if not all_healthy:
        return JSONResponse(
            status_code=503,
            content={"status": "degraded", "checks": checks},
        )

    return JSONResponse(
        status_code=200,
        content={"status": "ready", "checks": checks},
    )
