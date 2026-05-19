import re
from motor.motor_asyncio import AsyncIOMotorDatabase


class StockRepo:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.col = db["stocks"]

    async def find_all(self, skip: int = 0, limit: int = 100):
        cursor = self.col.find({}, {"_id": 0}).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)

    async def find_by_code(self, ts_code: str):
        return await self.col.find_one({"ts_code": ts_code}, {"_id": 0})

    async def search_by_name(self, keyword: str, limit: int = 20):
        cursor = self.col.find(
            {"$or": [{"name": {"$regex": re.escape(keyword), "$options": "i"}}, {"ts_code": {"$regex": re.escape(keyword), "$options": "i"}}]},
            {"_id": 0},
        ).limit(limit)
        return await cursor.to_list(length=limit)

    async def bulk_upsert(self, stocks: list[dict]) -> int:
        from pymongo import UpdateOne
        ops = []
        for s in stocks:
            ts_code = s["ts_code"]
            update_fields = {k: v for k, v in s.items() if k != "ts_code"}
            ops.append(
                UpdateOne(
                    {"ts_code": ts_code},
                    {"$set": update_fields, "$setOnInsert": {"industry": ""}},
                    upsert=True,
                )
            )
        result = await self.col.bulk_write(ops, ordered=False)
        return result.upserted_count + result.modified_count
