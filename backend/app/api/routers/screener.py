from fastapi import APIRouter, Depends
from app.models.response import BaseResponse
from app.models.screener import ScreenerRequest, AIParseRequest, AIPickRequest, AIAnalyzeRequest, AIChatRequest
from app.services.screener_service import ScreenerService
from app.services.screener_ai_service import ScreenerAIService
from app.api.deps import get_db
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter(prefix="/api/screener", tags=["筛选"])


async def get_screener_service(db: AsyncIOMotorDatabase = Depends(get_db)) -> ScreenerService:
    return ScreenerService(db)


async def get_ai_service(db: AsyncIOMotorDatabase = Depends(get_db)) -> ScreenerAIService:
    return ScreenerAIService(db)


@router.post("")
async def screen(
    req: ScreenerRequest,
    service: ScreenerService = Depends(get_screener_service),
):
    data = await service.screen(req.conditions, req.limit)
    return BaseResponse(data=data)


@router.get("/templates")
async def get_templates(
    service: ScreenerService = Depends(get_screener_service),
):
    data = await service.get_templates()
    return BaseResponse(data=data)


@router.get("/industries")
async def get_industries(
    service: ScreenerService = Depends(get_screener_service),
):
    data = await service.get_industries()
    return BaseResponse(data=data)


@router.post("/ai-parse")
async def ai_parse(
    req: AIParseRequest,
    ai_service: ScreenerAIService = Depends(get_ai_service),
):
    data = await ai_service.parse_natural_language(req.query)
    return BaseResponse(data=data)


@router.post("/ai-pick")
async def ai_pick(
    req: AIPickRequest,
    ai_service: ScreenerAIService = Depends(get_ai_service),
):
    data = await ai_service.ai_pick(req.query)
    return BaseResponse(data=data)


@router.post("/ai-analyze")
async def ai_analyze(
    req: AIAnalyzeRequest,
    ai_service: ScreenerAIService = Depends(get_ai_service),
):
    data = await ai_service.ai_analyze(req.ts_codes)
    return BaseResponse(data=data)


@router.get("/ai-daily")
async def ai_daily(
    ai_service: ScreenerAIService = Depends(get_ai_service),
):
    data = await ai_service.get_daily_recommendation()
    return BaseResponse(data=data)


@router.post("/ai-chat")
async def ai_chat(
    req: AIChatRequest,
    ai_service: ScreenerAIService = Depends(get_ai_service),
):
    data = await ai_service.ai_chat(req.query, req.history)
    return BaseResponse(data=data)
