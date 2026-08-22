import time
import uuid
import structlog
from starlette.types import ASGIApp, Receive, Scope, Send

logger = structlog.get_logger("metaradar.http")


class CorrelationIdMiddleware:
    """
    ASGI middleware that reads or generates X-Request-ID and X-Correlation-ID,
    binds them to structlog contextvars for async-safe log tracing, and emits
    structured request telemetry on completion.
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
