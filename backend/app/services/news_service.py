from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.repos.news_repo import NewsRepo


class NewsService:
    def __init__(self):
        self._repo = None

    def _get_repo(self) -> NewsRepo:
        if self._repo is None:
            client = AsyncIOMotorClient(settings.MONGO_URI)
            db = client[settings.MONGO_DB]
            self._repo = NewsRepo(db)
        return self._repo

    async def get_market_news(self, limit: int = 20, page: int = 1, news_type: Optional[str] = None) -> List[dict]:
        repo = self._get_repo()
        skip = (page - 1) * limit
        news = await repo.find_market_news(limit, skip, news_type)
        for n in news:
            n["id"] = n.get("url", "") or n.get("title", "")[:20]
        return news

    async def get_stock_news(self, ts_code: str, limit: int = 10) -> List[dict]:
        repo = self._get_repo()
        news = await repo.find_stock_news(ts_code, limit)
        for n in news:
            n["id"] = n.get("url", "") or n.get("title", "")[:20]
        return news

    async def get_hot_news(self, limit: int = 10) -> List[dict]:
        repo = self._get_repo()
        news = await repo.find_hot_news(limit)
        for n in news:
            n["id"] = n.get("url", "") or n.get("title", "")[:20]
        return news

    async def search_news(self, keyword: str, limit: int = 20) -> List[dict]:
        repo = self._get_repo()
        news = await repo.search_news(keyword, limit)
        for n in news:
            n["id"] = n.get("url", "") or n.get("title", "")[:20]
        return news

    async def get_sentiment_stats(self) -> dict:
        repo = self._get_repo()
        return await repo.get_sentiment_stats()
