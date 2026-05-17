import time
import uuid
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("app.access")


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:12])
        request.state.request_id = request_id
        start = time.monotonic()
        try:
            response = await call_next(request)
        except Exception:
            elapsed = (time.monotonic() - start) * 1000
            logger.error(f"[{request_id}] {request.method} {request.url.path} → ERROR, {elapsed:.1f}ms")
            raise
        elapsed = (time.monotonic() - start) * 1000
        logger.info(f"[{request_id}] {request.method} {request.url.path} → {response.status_code}, {elapsed:.1f}ms")
        response.headers["X-Request-ID"] = request_id
        return response


class SlowQueryMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, threshold_ms: int = 500):
        super().__init__(app)
        self.threshold_ms = threshold_ms

    async def dispatch(self, request: Request, call_next):
        start = time.monotonic()
        response = await call_next(request)
        elapsed = (time.monotonic() - start) * 1000
        if elapsed > self.threshold_ms:
            logger.warning(f"慢请求: {request.method} {request.url.path} {elapsed:.0f}ms")
        return response
