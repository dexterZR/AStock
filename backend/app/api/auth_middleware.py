"""
全局 API 鉴权中间件。
保护所有非公开端点，跳过健康检查、登录注册等公开路由。
"""
import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import jwt
from app.core.config import settings

logger = logging.getLogger("app.auth")

# 无需认证的公开路径
PUBLIC_PATHS = {
    "/api/health",
    "/api/auth/register",
    "/api/auth/login",
    "/",
    "/favicon.ico",
    "/docs",
    "/redoc",
    "/openapi.json",
}


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 放行公开路径（SSE 由自身的 cookie 认证处理）
        # 健康检查和调试端点无需认证
        is_public = (
            request.url.path in PUBLIC_PATHS
            or request.url.path.startswith("/api/sse/")
            or request.url.path.startswith("/api/health/")
        )
        if is_public:
            return await call_next(request)

        # 检查 Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(status_code=401, content={"success": False, "code": "UNAUTHORIZED", "message": "未登录"})

        token = auth_header[len("Bearer "):]
        try:
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
            request.state.current_user = payload
        except jwt.ExpiredSignatureError:
            return JSONResponse(status_code=401, content={"success": False, "code": "TOKEN_EXPIRED", "message": "Token 已过期"})
        except jwt.InvalidTokenError:
            return JSONResponse(status_code=401, content={"success": False, "code": "INVALID_TOKEN", "message": "Token 无效"})

        return await call_next(request)
