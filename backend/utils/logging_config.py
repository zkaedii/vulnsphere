"""
Structured Logging Configuration for VulnSphere PRIME

Uses structlog for structured, JSON-formatted logging.
Supports correlation IDs for request tracing.
"""
import logging
import sys
import uuid
from contextvars import ContextVar
from datetime import datetime
from typing import Any, Dict, Optional

import structlog
from structlog.types import Processor

# Context variable for request correlation
correlation_id_var: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)


def get_correlation_id() -> str:
    """Get current correlation ID or generate new one"""
    cid = correlation_id_var.get()
    if cid is None:
        cid = str(uuid.uuid4())[:8]
        correlation_id_var.set(cid)
    return cid


def set_correlation_id(cid: str) -> None:
    """Set correlation ID for current context"""
    correlation_id_var.set(cid)


def add_correlation_id(
    logger: logging.Logger,
    method_name: str,
    event_dict: Dict[str, Any]
) -> Dict[str, Any]:
    """Add correlation ID to log event"""
    event_dict['correlation_id'] = get_correlation_id()
    return event_dict


def add_timestamp(
    logger: logging.Logger,
    method_name: str,
    event_dict: Dict[str, Any]
) -> Dict[str, Any]:
    """Add ISO timestamp to log event"""
    event_dict['timestamp'] = datetime.utcnow().isoformat() + 'Z'
    return event_dict


def add_service_info(
    logger: logging.Logger,
    method_name: str,
    event_dict: Dict[str, Any]
) -> Dict[str, Any]:
    """Add service information to log event"""
    event_dict['service'] = 'vulnsphere-prime'
    event_dict['version'] = '1.0.0'
    return event_dict


def configure_logging(
    log_level: str = "INFO",
    json_format: bool = True,
    development: bool = False
) -> None:
    """
    Configure structured logging for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        json_format: Output as JSON (True) or human-readable (False)
        development: Enable development-friendly formatting
    """
    # Shared processors
    shared_processors: list[Processor] = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        add_timestamp,
        add_correlation_id,
        add_service_info,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if development:
        # Development: colorful console output
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True)
        ]
    elif json_format:
        # Production: JSON output
        processors = shared_processors + [
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer()
        ]
    else:
        # Plain text output
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=False)
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )

    # Suppress noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str = None) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.

    Usage:
        logger = get_logger(__name__)
        logger.info("scan_started", network_size=1000, engine="boosted")
    """
    return structlog.get_logger(name)


# Pre-configured loggers for common components
class LoggerMixin:
    """Mixin class to add logging capability to any class"""

    @property
    def logger(self) -> structlog.stdlib.BoundLogger:
        if not hasattr(self, '_logger'):
            self._logger = get_logger(self.__class__.__name__)
        return self._logger


# Logging utilities for scan operations
class ScanLogger:
    """Specialized logger for scan operations"""

    def __init__(self, scan_id: str):
        self.scan_id = scan_id
        self.logger = get_logger("scan")
        self.start_time = datetime.utcnow()

    def log_start(self, network_size: int, engine: str, **kwargs):
        """Log scan start"""
        self.logger.info(
            "scan_started",
            scan_id=self.scan_id,
            network_size=network_size,
            engine=engine,
            **kwargs
        )

    def log_progress(self, iteration: int, max_iterations: int, energy: float, phase: str):
        """Log scan progress"""
        progress = (iteration / max_iterations) * 100
        self.logger.debug(
            "scan_progress",
            scan_id=self.scan_id,
            iteration=iteration,
            progress_pct=round(progress, 1),
            energy=round(energy, 4),
            phase=phase
        )

    def log_complete(
        self,
        vulnerabilities: int,
        iterations: int,
        speedup: float,
        converged: bool
    ):
        """Log scan completion"""
        elapsed = (datetime.utcnow() - self.start_time).total_seconds()
        self.logger.info(
            "scan_completed",
            scan_id=self.scan_id,
            vulnerabilities_found=vulnerabilities,
            iterations=iterations,
            speedup_factor=round(speedup, 2),
            converged=converged,
            duration_seconds=round(elapsed, 2)
        )

    def log_error(self, error: Exception, context: Dict[str, Any] = None):
        """Log scan error"""
        self.logger.error(
            "scan_error",
            scan_id=self.scan_id,
            error_type=type(error).__name__,
            error_message=str(error),
            context=context or {}
        )


# FastAPI middleware for request logging
class RequestLoggingMiddleware:
    """Middleware for logging HTTP requests"""

    def __init__(self, app):
        self.app = app
        self.logger = get_logger("http")

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Generate correlation ID
        correlation_id = str(uuid.uuid4())[:8]
        set_correlation_id(correlation_id)

        start_time = datetime.utcnow()

        # Log request
        self.logger.info(
            "request_started",
            method=scope["method"],
            path=scope["path"],
            correlation_id=correlation_id
        )

        # Process request
        status_code = 500
        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            # Log response
            elapsed = (datetime.utcnow() - start_time).total_seconds() * 1000
            self.logger.info(
                "request_completed",
                method=scope["method"],
                path=scope["path"],
                status_code=status_code,
                duration_ms=round(elapsed, 2),
                correlation_id=correlation_id
            )
