"""
Rate limiting middleware using Redis atomic counter.
Limits: 120 requests per minute per IP by default.
"""
import logging
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.database import redis_client

logger = logging.getLogger("app.ratelimit")

_RATE_LIMIT_SCRIPT = """
local key = KEYS[1]
local max = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local current = redis.call('INCR', key)
if current == 1 then
    redis.call('EXPIRE', key, window)
end
if current > max then
    return 0
end
return 1
"""


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = 120, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._sha: str | None = None

    async def dispatch(self, request: Request, call_next):
        if request.url.path in ('/api/health', '/', '/favicon.ico'):
            return await call_next(request)

        client_ip = request.client.host if request.client else 'unknown'
        key = f'ratelimit:{client_ip}'

        try:
            redis = redis_client
            if redis:
                if not self._sha:
                    self._sha = await redis.script_load(_RATE_LIMIT_SCRIPT)
                allowed = await redis.evalsha(self._sha, 1, key, self.max_requests, self.window_seconds)
                if not allowed:
                    raise HTTPException(status_code=429, detail='请求过于频繁，请稍后再试')
        except HTTPException:
            raise
        except Exception:
            logger.warning("Redis 不可用，限流已降级: client_ip=%s", client_ip, exc_info=True)

        return await call_next(request)
