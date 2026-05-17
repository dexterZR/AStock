from fastapi import APIRouter
from typing import Optional
from app.services.news_service import NewsService


router = APIRouter(prefix="/news", tags=["新闻资讯"])

news_service = NewsService()


@router.get("/market")
async def get_market_news(
    limit: int = 20,
    page: int = 1,
    news_type: Optional[str] = None
):
    """获取市场新闻"""
    data = await news_service.get_market_news(limit, page, news_type)
    return {"success": True, "data": data, "message": ""}


@router.get("/stock/{ts_code}")
async def get_stock_news(ts_code: str, limit: int = 10):
    """获取个股相关新闻"""
    data = await news_service.get_stock_news(ts_code, limit)
    return {"success": True, "data": data, "message": ""}


@router.get("/hot")
async def get_hot_news(limit: int = 10):
    """获取热点新闻"""
    data = await news_service.get_hot_news(limit)
    return {"success": True, "data": data, "message": ""}


@router.get("/search")
async def search_news(keyword: str, limit: int = 20):
    """搜索新闻"""
    data = await news_service.search_news(keyword, limit)
    return {"success": True, "data": data, "message": ""}
