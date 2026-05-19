import uuid
import traceback
import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = logging.getLogger("app")


class AppError(Exception):
    def __init__(self, message: str, code: str = "INTERNAL_ERROR", status_code: int = 500, details: dict = None):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


class NotFoundError(AppError):
    def __init__(self, message="资源不存在"):
        super().__init__(message, "NOT_FOUND", 404)


class ValidationError(AppError):
    def __init__(self, message="参数校验失败", details=None):
        super().__init__(message, "VALIDATION_ERROR", 422, details)


class ExternalAPIError(AppError):
    def __init__(self, message="外部数据源异常"):
        super().__init__(message, "EXTERNAL_API_ERROR", 502)


def register_exception_handlers(app):
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
                "request_id": getattr(request.state, "request_id", ""),
            },
        )

    @app.exception_handler(ConnectionError)
    async def connection_error_handler(request: Request, exc: ConnectionError):
        request_id = getattr(request.state, "request_id", str(uuid.uuid4())[:12])
        logger.warning(f"[{request_id}] 连接数超限: {exc}")
        return JSONResponse(
            status_code=503,
            content={
                "success": False,
                "code": "SERVICE_UNAVAILABLE",
                "message": str(exc),
                "request_id": request_id,
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        request_id = getattr(request.state, "request_id", str(uuid.uuid4())[:12])
        logger.critical(f"[{request_id}] 未处理异常: {exc}\n{traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "code": "INTERNAL_ERROR",
                "message": "服务器内部错误，请稍后重试",
                "request_id": request_id,
            },
        )
