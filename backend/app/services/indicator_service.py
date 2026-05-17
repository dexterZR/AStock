from motor.motor_asyncio import AsyncIOMotorDatabase


class IndicatorService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def get_indicators(self, ts_code: str, limit: int = 60):
        cursor = self.db["indicators"].find(
            {"ts_code": ts_code},
            {"_id": 0},
        ).sort("trade_date", -1).limit(limit)
        return await cursor.to_list(length=limit)

    async def get_latest_indicator(self, ts_code: str):
        return await self.db["indicators"].find_one(
            {"ts_code": ts_code},
            {"_id": 0},
            sort=[("trade_date", -1)],
        )
