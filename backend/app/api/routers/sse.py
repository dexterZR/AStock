import uuid
import logging
from fastapi import APIRouter, Request, Query, Depends, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
import jwt
from app.core.config import settings
from app.infrastructure.sse_manager import SSEManager

logger = logging.getLogger("app.sse")
router = APIRouter(prefix="/api/sse", tags=["实时推送"])


def get_sse_manager(request: Request) -> SSEManager:
    return request.app.state.sse_manager


def get_current_user_from_cookie(request: Request) -> dict:
    """从 Cookie 中读取 JWT 进行认证"""
    token = request.cookies.get("astock_token")
    if not token:
        raise HTTPException(status_code=401, detail="未登录")
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token 已过期")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token 无效")


@router.get("/quotes/stream")
async def quote_stream(
    request: Request,
    ts_codes: str = Query(default="", description="订阅股票代码，逗号分隔"),
    mgr: SSEManager = Depends(get_sse_manager),
    user: dict = Depends(get_current_user_from_cookie),
):
    logger.info("SSE 连接建立: user=%s", user.get("username"))
    client_id = str(uuid.uuid4())
    if ts_codes:
        for code in ts_codes.split(","):
            mgr.subscribe(client_id, f"quote:{code.strip()}")

    # 连接检查在 event_generator 内部执行，ConnectionError 会以 503 返回
    return StreamingResponse(
        mgr.event_generator(client_id, request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
