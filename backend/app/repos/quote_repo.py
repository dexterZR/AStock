from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import UpdateOne


class QuoteRepo:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.col = db["daily_quotes"]

    async def find_daily(self, ts_code: str, start_date: str, end_date: str, limit: int = 5000):
        query = {"ts_code": ts_code, "trade_date": {"$gte": start_date, "$lte": end_date}, "adjust_flag": "none"}
        cursor = self.col.find(query, {"_id": 0}).sort("trade_date", 1)
        return await cursor.to_list(length=limit)

    async def find_latest(self, ts_code: str):
        return await self.col.find_one(
            {"ts_code": ts_code, "adjust_flag": "none"}, {"_id": 0}, sort=[("trade_date", -1)]
        )

    async def find_previous(self, ts_code: str, current_date: str):
        return await self.col.find_one(
            {"ts_code": ts_code, "trade_date": {"$lt": current_date}, "adjust_flag": "none"},
            {"_id": 0, "close": 1}, sort=[("trade_date", -1)]
        )

    async def bulk_upsert(self, records: list[dict]) -> int:
        ops = [
            UpdateOne(
                {"ts_code": r["ts_code"], "trade_date": r["trade_date"]},
                {"$set": r},
                upsert=True,
            )
            for r in records
        ]
        result = await self.col.bulk_write(ops, ordered=False)
        return result.upserted_count + result.modified_count
