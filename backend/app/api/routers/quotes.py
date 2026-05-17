from fastapi import APIRouter, Depends, Query
from app.models.response import BaseResponse
from app.services.quote_service import QuoteService
from app.repos.quote_repo import QuoteRepo
from app.infrastructure.cache import RedisCache
from app.api.deps import get_db, get_redis
from motor.motor_asyncio import AsyncIOMotorDatabase
from redis.asyncio import Redis

router = APIRouter(prefix="/api/quotes", tags=["行情"])


async def get_quote_service(
    db: AsyncIOMotorDatabase = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> QuoteService:
    return QuoteService(QuoteRepo(db), RedisCache(redis))


@router.get("/daily/{ts_code}")
async def get_daily(
    ts_code: str,
    start_date: str = Query(..., description="开始日期 YYYYMMDD"),
    end_date: str = Query(None, description="结束日期 YYYYMMDD"),
    service: QuoteService = Depends(get_quote_service),
):
    from datetime import datetime
    if not end_date:
        end_date = datetime.now().strftime("%Y%m%d")
    data = await service.get_daily_quotes(ts_code, start_date, end_date)
    return BaseResponse(data=data)


@router.get("/latest/{ts_code}")
async def get_latest(ts_code: str, service: QuoteService = Depends(get_quote_service)):
    data = await service.get_latest_quote(ts_code)
    return BaseResponse(data=data)


@router.get("/minute/{ts_code}")
async def get_minute(
    ts_code: str,
    period: str = Query("5", description="1/5/15/30/60"),
    limit: int = Query(240, ge=1, le=1000),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    cursor = db["minute_quotes"].find(
        {"ts_code": ts_code, "period": period},
        {"_id": 0},
    ).sort("trade_time", -1).limit(limit)
    data = await cursor.to_list(length=limit)
    data.reverse()
    return BaseResponse(data=data)
