"""API middleware for request tracing."""

import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


class RequestTraceMiddleware(BaseHTTPMiddleware):
    """Middleware to inject Request ID and Correlation ID into every request.

    - X-Request-ID: generated per-request if not provided.
    - X-Correlation-ID: propagated from caller or generated.

    Both IDs are bound to structlog context for the duration of the request.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        correlation_id = request.headers.get("x-correlation-id", str(uuid.uuid4()))

        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            correlation_id=correlation_id,
        )

        response = await call_next(request)

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Correlation-ID"] = correlation_id

        structlog.contextvars.unbind_contextvars("request_id", "correlation_id")

        return response
