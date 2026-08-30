import time
import uuid
import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send
from fastapi import Request

logger = structlog.get_logger("metaradar.http")


class CorrelationIdMiddleware:
    """
    ASGI middleware that reads or generates X-Request-ID and X-Correlation-ID,
    binds them to structlog contextvars for async-safe log tracing,
    populates request.state.correlation_id for FastAPI endpoints,
    and emits structured request telemetry on completion.
    """

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Clear prior task context
        structlog.contextvars.clear_contextvars()

        # Extract or generate correlation ID
        headers_dict = dict(scope.get("headers", []))
        raw_request_id = headers_dict.get(b"x-request-id", b"").decode("utf-8", "ignore").strip()
        raw_correlation_id = headers_dict.get(b"x-correlation-id", b"").decode("utf-8", "ignore").strip()

        request_id = raw_request_id or f"req-{uuid.uuid4().hex[:12]}"
        correlation_id = raw_correlation_id or request_id

        # Bind to Starlette/FastAPI request.state
        if "state" not in scope:
            scope["state"] = {}
        scope["state"]["request_id"] = request_id
        scope["state"]["correlation_id"] = correlation_id

        # Bind to async contextvars for structured logger
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            correlation_id=correlation_id,
            path=scope.get("path", ""),
            method=scope.get("method", "UNKNOWN"),
        )

        start_time = time.perf_counter()
        status_code = 500

        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 200)
                headers_list = list(message.get("headers", []))
                headers_list.append((b"x-request-id", request_id.encode("utf-8")))
                headers_list.append((b"x-correlation-id", correlation_id.encode("utf-8")))
                message = {**message, "headers": headers_list}
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.info(
                "http_request_completed",
                status_code=status_code,
                duration_ms=duration_ms,
            )


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Injects baseline hardened Content-Security-Policy, nosniff, DENY, and strict referrer headers.
    """
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "object-src 'none'; "
            "base-uri 'none'; "
            "frame-ancestors 'none'; "
            "form-action 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self';"
        )
        return response
