from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.api.deps import get_db
from app.services.sector_service import SectorAnalysisService


router = APIRouter(prefix="/sector", tags=["板块分析"])


@router.get("/ranking")
async def get_sector_ranking(
    limit: int = 20,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """获取行业板块涨跌排行"""
    service = SectorAnalysisService(db)
    data = await service.get_sector_ranking(limit)
    return {"success": True, "data": data, "message": ""}


@router.get("/concept-ranking")
async def get_concept_ranking(
    limit: int = 20,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """获取概念板块涨跌排行"""
    service = SectorAnalysisService(db)
    data = await service.get_concept_ranking(limit)
    return {"success": True, "data": data, "message": ""}


@router.get("/related/{ts_code}")
async def get_stock_related_sectors(
    ts_code: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """获取个股相关板块及同板块联动"""
    service = SectorAnalysisService(db)
    data = await service.get_stock_related_sectors(ts_code)
    return {"success": True, "data": data, "message": ""}


@router.get("/cons/{sector_name}")
async def get_sector_constituents(
    sector_name: str,
    limit: int = 20,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """获取板块成分股（从同花顺实时数据）"""
    service = SectorAnalysisService(db)
    data = await service.get_sector_constituents(sector_name, limit)
    return {"success": True, "data": data, "message": ""}


@router.get("/market-overview-extended")
async def get_market_overview_extended(
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """获取扩展市场概览（涨跌家数、市场温度）"""
    service = SectorAnalysisService(db)
    data = await service.get_market_overview_extended()
    return {"success": True, "data": data, "message": ""}
