from fastapi import APIRouter, Depends
from typing import List
from app.models.response import BaseResponse
from app.services.analysis_service import MultiAgentAnalysisService
from app.api.deps import get_db
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter(prefix="/api/analysis", tags=["AI分析"])


async def get_analysis_service(db: AsyncIOMotorDatabase = Depends(get_db)) -> MultiAgentAnalysisService:
    return MultiAgentAnalysisService(db)


@router.post("/batch")
async def analyze_batch(
    ts_codes: List[str],
    service: MultiAgentAnalysisService = Depends(get_analysis_service),
):
    """批量分析股票列表"""
    if len(ts_codes) > 20:
        ts_codes = ts_codes[:20]
    data = await service.analyze_batch(ts_codes)
    return BaseResponse(data=data)


@router.get("/{ts_code}")
async def analyze_single(
    ts_code: str,
    service: MultiAgentAnalysisService = Depends(get_analysis_service),
):
    """单股票分析"""
    data = await service.analyze_stock(ts_code)
    return BaseResponse(data=data)
