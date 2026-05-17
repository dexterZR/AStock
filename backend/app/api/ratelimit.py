"""
Rate limiting middleware using Redis sliding window.
Limits: 60 requests per minute per IP by default.
"""
import time
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.database import redis_client


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = 60, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health check and static files
        if request.url.path in ('/api/health', '/', '/favicon.ico'):
            return await call_next(request)

        client_ip = request.client.host if request.client else 'unknown'
        key = f'ratelimit:{client_ip}'

        try:
            redis = redis_client
            if redis:
                current = await redis.get(key)
                if current and int(current) >= self.max_requests:
                    raise HTTPException(status_code=429, detail='请求过于频繁，请稍后再试')

                pipe = redis.pipeline()
                pipe.incr(key)
                pipe.expire(key, self.window_seconds)
                await pipe.execute()
        except HTTPException:
            raise
        except Exception:
            # If Redis is unavailable, skip rate limiting
            pass

        return await call_next(request)
