import time
import uuid
from urllib.parse import urlparse
import logging
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings

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


class CSRFMiddleware(BaseHTTPMiddleware):
    """校验非 GET/HEAD 请求的 Origin/Referer，防止 CSRF 攻击。"""

    async def dispatch(self, request: Request, call_next):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return await call_next(request)

        origin = request.headers.get("Origin")
        referer = request.headers.get("Referer")
        allowed_origins = [urlparse(o).hostname for o in settings.CORS_ORIGINS if urlparse(o).hostname]

        # localhost 请求跳过校验（开发环境）
        if not allowed_origins or all(h in ("localhost", "127.0.0.1") for h in allowed_origins):
            return await call_next(request)

        check_value = origin or referer or ""
        if not check_value:
            logger.warning("CSRF: 缺少 Origin 和 Referer: %s %s", request.method, request.url.path)
            raise HTTPException(status_code=403, detail="请求被拒绝：缺少来源信息")

        request_host = urlparse(check_value).hostname
        if request_host and request_host not in allowed_origins:
            logger.warning(
                "CSRF: 非法来源 %s, 请求: %s %s", request_host, request.method, request.url.path,
            )
            raise HTTPException(status_code=403, detail="请求被拒绝：非法来源")

        return await call_next(request)
