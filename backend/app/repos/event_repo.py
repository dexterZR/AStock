from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Optional
class EventRepo:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    async def find_events(self, ts_code: Optional[str] = None, days: int = 30):
        from datetime import datetime, timedelta
        query = {}; 
        if ts_code: query["ts_code"] = ts_code
        if days:
            cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
            query["event_date"] = {"$gte": cutoff}
        return await self.db["stock_events"].find(query, {"_id": 0}).sort("event_date", -1).to_list(None)
    async def insert_event(self, event: dict):
        r = await self.db["stock_events"].insert_one(event)
        return str(r.inserted_id)
    async def find_alerts(self, acknowledged: Optional[bool] = None):
        query = {}
        if acknowledged is not None: query["is_acknowledged"] = acknowledged
        return await self.db["risk_alerts"].find(query, {"_id": 0}).sort("triggered_at", -1).to_list(None)
