"""Structured logging setup."""
import structlog
import logging
import sys


def setup_logging(level: str = "INFO"):
    """Configure structlog for JSON output in production, pretty in dev."""
    is_prod = level == "INFO" or level == "WARNING" or level == "ERROR"

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer() if is_prod else structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.DEBUG if level == "DEBUG" else logging.INFO
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )   