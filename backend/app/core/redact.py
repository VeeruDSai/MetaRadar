"""Redact secrets from error strings, log messages, and query-param dumps."""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, Mapping, Optional

SENSITIVE_KEYS = {
    "password", "token", "api_key", "secret", "authorization",
    "cookie", "access_token", "private_key", "bearer", "grok_key",
    "apikey", "client_secret", "jwt",
}

_KV_RE = re.compile(
    r"(?i)(?P<key>api[_-]?key|password|token|secret|authorization|access_token|bearer|private_key|client_secret|jwt)"
    r"(?P<sep>\s*[:=]\s*)(?P<val>[^\s,;\"'&}]+)"
)
_QUOTED_RE = re.compile(
    r"(?i)(['\"]?(?P<key>api[_-]?key|password|token|secret|authorization|access_token)['\"]?\s*[:=]\s*)(['\"])(?P<val>[^'\"]+)\3"
)


def redact_value(key: str, value: Any) -> Any:
    lowered = key.lower().replace("-", "_")
    if any(s in lowered for s in SENSITIVE_KEYS):
        return "[REDACTED_SECRET]"
    return value


def redact_mapping(params: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    """Return a copy of params with secret-named keys redacted."""
    if not params:
        return {}
    return {str(k): redact_value(str(k), v) for k, v in params.items()}


def redact_text(text: str) -> str:
    """Redact secret-looking key/value pairs in a free-form string."""
    if not text:
        return text
    redacted = _QUOTED_RE.sub(r"\1\3[REDACTED_SECRET]\3", text)
    redacted = _KV_RE.sub(lambda m: f"{m.group('key')}{m.group('sep')}[REDACTED_SECRET]", redacted)
    return redacted


class SecretScrubFilter(logging.Filter):
    """Applies redact_text to stdlib log records so secret scrubbing is not structlog-only."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            if isinstance(record.msg, str):
                record.msg = redact_text(record.msg)
            if record.args:
                if isinstance(record.args, dict):
                    record.args = redact_mapping(record.args)
                elif isinstance(record.args, tuple):
                    record.args = tuple(
                        redact_text(a) if isinstance(a, str) else a for a in record.args
                    )
        except Exception:
            return True
        return True
