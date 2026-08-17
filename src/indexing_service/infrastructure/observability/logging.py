"""Structured logging configuration with structlog."""

import logging
import sys

import structlog


def configure_logging(
    log_level: str = "INFO",
    log_format: str = "json",
    service_name: str = "indexing-service",
) -> None:
    """Configure structlog for structured logging.

    Args:
        log_level: Log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_format: Output format - 'json' for production, 'console' for development.
        service_name: Service name to bind to all log entries.
    """
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if log_format == "json":
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level.upper())

    # Silence noisy third-party loggers
    for logger_name in ("uvicorn.access", "sqlalchemy.engine", "httpcore", "httpx"):
        logging.getLogger(logger_name).setLevel(logging.WARNING)

    # Bind service_name to all loggers
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(service=service_name)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a bound structlog logger.

    Args:
        name: Logger name, typically __name__ of the calling module.

    Returns:
        A bound structlog logger instance.
    """
    logger: structlog.stdlib.BoundLogger = structlog.get_logger(name)
    return logger
