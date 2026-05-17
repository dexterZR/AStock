from motor.motor_asyncio import AsyncIOMotorDatabase
class IndicatorRepo:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.col = db["indicators"]
    async def find_by_code(self, ts_code: str, limit: int = 60):
        cursor = self.col.find({"ts_code": ts_code}, {"_id": 0}).sort("trade_date", -1).limit(limit)
        return await cursor.to_list(length=limit)
    async def find_latest_by_code(self, ts_code: str):
        return await self.col.find_one({"ts_code": ts_code}, {"_id": 0}, sort=[("trade_date", -1)])
