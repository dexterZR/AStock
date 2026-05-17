from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import UpdateOne
from typing import List, Optional
from datetime import datetime


class NewsRepo:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.col = db["news"]

    async def bulk_upsert(self, records: List[dict]) -> int:
        if not records:
            return 0
        ops = []
        for r in records:
            url = r.get("url", "")
            filter_doc = {"url": url} if url else {"title": r.get("title", ""), "pub_date": r.get("pub_date", "")}
            ops.append(UpdateOne(filter_doc, {"$set": r}, upsert=True))
        result = await self.col.bulk_write(ops, ordered=False)
        return result.modified_count + result.upserted_count

    async def find_market_news(self, limit: int = 20, skip: int = 0, news_type: Optional[str] = None) -> List[dict]:
        query = {}
        if news_type:
            query["type"] = news_type
        cursor = self.col.find(query, {"_id": 0}).sort("pub_date", -1).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)

    async def find_hot_news(self, limit: int = 10) -> List[dict]:
        cursor = self.col.find({}, {"_id": 0}).sort("heat_score", -1).limit(limit)
        return await cursor.to_list(length=limit)

    async def find_stock_news(self, ts_code: str, limit: int = 10) -> List[dict]:
        symbol = ts_code.split(".")[0]
        cursor = self.col.find(
            {"$or": [
                {"related_codes": symbol},
                {"title": {"$regex": symbol}},
            ]},
            {"_id": 0}
        ).sort("pub_date", -1).limit(limit)
        return await cursor.to_list(length=limit)

    async def search_news(self, keyword: str, limit: int = 20) -> List[dict]:
        cursor = self.col.find(
            {"$or": [
                {"title": {"$regex": keyword, "$options": "i"}},
                {"summary": {"$regex": keyword, "$options": "i"}},
            ]},
            {"_id": 0}
        ).sort("pub_date", -1).limit(limit)
        return await cursor.to_list(length=limit)

    async def get_sentiment_stats(self) -> dict:
        pipeline = [
            {"$group": {
                "_id": "$sentiment",
                "count": {"$sum": 1},
            }},
        ]
        results = await self.col.aggregate(pipeline).to_list(length=None)
        stats = {"positive": 0, "neutral": 0, "negative": 0}
        for r in results:
            key = r["_id"]
            if key in stats:
                stats[key] = r["count"]
        return stats

    async def count_documents(self, query: dict = None) -> int:
        return await self.col.count_documents(query or {})

    async def delete_old_news(self, days: int = 30):
        from datetime import timedelta
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        result = await self.col.delete_many({"pub_date": {"$lt": cutoff}})
        return result.deleted_count
