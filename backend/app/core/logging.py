import logging
import os
import sys
import structlog
from typing import Any, Dict

from app.core.redact import SENSITIVE_KEYS, SecretScrubFilter, redact_text


def _scrub_secrets(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Scrub sensitive keys and tokens from log event dictionary."""
    for key in list(event_dict.keys()):
        if any(s in key.lower() for s in SENSITIVE_KEYS):
            event_dict[key] = "[REDACTED_SECRET]"
        elif "email" in key.lower():
            event_dict[key] = "[REDACTED_PII]"
        elif isinstance(event_dict[key], str):
            event_dict[key] = redact_text(event_dict[key])
    return event_dict


def configure_structlog(json_logs: bool = True) -> None:
    """Configure structured JSON logging across FastAPI and background services."""
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        _scrub_secrets,
    ]

    if json_logs:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    root = logging.getLogger()
    if not any(isinstance(f, SecretScrubFilter) for f in root.filters):
        root.addFilter(SecretScrubFilter())


def get_logger(name: str = "metaradar") -> Any:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


# Default configuration on import
configure_structlog(json_logs=True)
logger = get_logger("metaradar")
