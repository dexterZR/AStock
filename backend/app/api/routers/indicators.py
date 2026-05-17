from fastapi import APIRouter, Depends, Query
from app.models.response import BaseResponse
from app.services.indicator_service import IndicatorService
from app.api.deps import get_db
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter(prefix="/api/indicators", tags=["技术指标"])


async def get_indicator_service(db: AsyncIOMotorDatabase = Depends(get_db)) -> IndicatorService:
    return IndicatorService(db)


@router.get("/{ts_code}")
async def get_indicators(
    ts_code: str,
    limit: int = Query(60, ge=1, le=500),
    service: IndicatorService = Depends(get_indicator_service),
):
    data = await service.get_indicators(ts_code, limit)
    return BaseResponse(data=data)


@router.get("/{ts_code}/latest")
async def get_latest_indicator(
    ts_code: str,
    service: IndicatorService = Depends(get_indicator_service),
):
    data = await service.get_latest_indicator(ts_code)
    return BaseResponse(data=data)
