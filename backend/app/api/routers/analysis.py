from fastapi import APIRouter, Depends, Query
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
    skip_llm: bool = Query(True, description="跳过LLM深度报告（讨论视图不需要LLM，大幅加速）"),
    service: MultiAgentAnalysisService = Depends(get_analysis_service),
):
    """批量分析股票列表（讨论面板用，默认跳过LLM以加速响应）"""
    if len(ts_codes) > 20:
        ts_codes = ts_codes[:20]
    data = await service.analyze_batch(ts_codes, skip_llm=skip_llm)
    return BaseResponse(data=data)


@router.get("/{ts_code}")
async def analyze_single(
    ts_code: str,
    skip_llm: bool = Query(False, description="是否跳过LLM深度报告"),
    service: MultiAgentAnalysisService = Depends(get_analysis_service),
):
    """单股票分析"""
    data = await service.analyze_stock(ts_code, skip_llm=skip_llm)
    return BaseResponse(data=data)
