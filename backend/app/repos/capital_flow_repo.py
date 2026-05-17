from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Optional


class CapitalFlowRepo:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.col = db["capital_flow"]

    async def find_latest_by_code(self, ts_code: str) -> Optional[dict]:
        return await self.col.find_one(
            {"ts_code": ts_code},
            {"_id": 0},
            sort=[("trade_date", -1)],
        )

    async def find_latest_batch(self, ts_codes: List[str]) -> List[dict]:
        pipeline = [
            {"$match": {"ts_code": {"$in": ts_codes}}},
            {"$sort": {"trade_date": -1}},
            {"$group": {"_id": "$ts_code", "latest": {"$first": "$$ROOT"}}},
            {"$replaceRoot": {"newRoot": "$latest"}},
            {"$project": {"_id": 0}},
        ]
        cursor = self.col.aggregate(pipeline)
        return await cursor.to_list(length=len(ts_codes))
