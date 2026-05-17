import uuid
from fastapi import APIRouter, Request, Query, Depends
from fastapi.responses import StreamingResponse
from app.infrastructure.sse_manager import SSEManager

router = APIRouter(prefix="/api/sse", tags=["实时推送"])


def get_sse_manager(request: Request) -> SSEManager:
    return request.app.state.sse_manager


@router.get("/quotes/stream")
async def quote_stream(
    request: Request,
    ts_codes: str = Query(default="", description="订阅股票代码，逗号分隔"),
    mgr: SSEManager = Depends(get_sse_manager),
):
    client_id = str(uuid.uuid4())
    if ts_codes:
        for code in ts_codes.split(","):
            mgr.subscribe(client_id, f"quote:{code.strip()}")

    return StreamingResponse(
        mgr.event_generator(client_id, request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
