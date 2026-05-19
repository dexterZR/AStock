from typing import List, Dict, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timedelta


class EventService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def add_event(self, event: dict) -> str:
        existing = await self.db["stock_events"].find_one({
            "ts_code": event["ts_code"],
            "event_type": event["event_type"],
            "event_date": event["event_date"],
        })
        if existing:
            return str(existing["_id"])

        result = await self.db["stock_events"].insert_one(event)

        if event.get("severity") in ["warning", "critical"]:
            await self._create_alert_from_event(event)

        return str(result.inserted_id)

    async def _create_alert_from_event(self, event: dict):
        alert = {
            "ts_code": event["ts_code"],
            "name": event["name"],
            "alert_type": "event",
            "alert_level": "high" if event["severity"] == "critical" else "medium",
            "title": f"[{event['event_type']}] {event['title']}",
            "description": event["content"],
            "source": event.get("source", ""),
            "triggered_at": datetime.now().isoformat(),
            "is_acknowledged": False,
            "related_event_id": str(event.get("_id", "")),
        }
        await self.db["risk_alerts"].insert_one(alert)

    async def get_events(self, ts_code: Optional[str] = None, days: int = 30) -> List[Dict]:
        query = {}
        if ts_code:
            query["ts_code"] = ts_code
        if days:
            cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
            query["event_date"] = {"$gte": cutoff}

        cursor = self.db["stock_events"].find(query, {"_id": 0}).sort("event_date", -1)
        return await cursor.to_list(None)

    async def get_unresolved_events(self, ts_codes: List[str]) -> List[Dict]:
        cursor = self.db["stock_events"].find({
            "ts_code": {"$in": ts_codes},
            "is_resolved": False,
            "severity": {"$in": ["warning", "critical"]},
        }, {"_id": 0}).sort("event_date", -1)
        return await cursor.to_list(None)

    async def mark_event_resolved(self, event_id: str):
        from bson import ObjectId
        await self.db["stock_events"].update_one(
            {"_id": ObjectId(event_id)},
            {"$set": {"is_resolved": True, "resolved_date": datetime.now().strftime("%Y%m%d")}}
        )

    async def get_risk_alerts(self, acknowledged: Optional[bool] = None) -> List[Dict]:
        query = {}
        if acknowledged is not None:
            query["is_acknowledged"] = acknowledged
        cursor = self.db["risk_alerts"].find(query).sort("triggered_at", -1)
        alerts = await cursor.to_list(None)

        missing_source = [a for a in alerts if not a.get("source") and a.get("related_event_id")]
        if missing_source:
            from bson import ObjectId
            event_ids = []
            for a in missing_source:
                try:
                    event_ids.append(ObjectId(a["related_event_id"]))
                except Exception:
                    pass
            if event_ids:
                events = await self.db["stock_events"].find(
                    {"_id": {"$in": event_ids}}, {"source": 1}
                ).to_list(None)
                event_map = {str(e["_id"]): e.get("source", "") for e in events}
                for a in missing_source:
                    src = event_map.get(a["related_event_id"], "")
                    if src:
                        a["source"] = src

        for a in alerts:
            a["_id"] = str(a.get("_id", ""))

        return alerts

    async def acknowledge_alert(self, alert_id: str):
        from bson import ObjectId
        await self.db["risk_alerts"].update_one(
            {"_id": ObjectId(alert_id)},
            {"$set": {"is_acknowledged": True, "acknowledged_at": datetime.now().isoformat()}}
        )

    async def generate_daily_brief(self, ts_codes: List[str]) -> Dict:
        events = await self.get_unresolved_events(ts_codes)
        alerts = await self.db["risk_alerts"].find({
            "ts_code": {"$in": ts_codes},
            "is_acknowledged": False,
        }, {"_id": 0}).to_list(None)

        # 批量查询最新行情（N+1 → 1次）
        quotes = []
        if ts_codes:
            pipeline = [
                {"$match": {"ts_code": {"$in": ts_codes}}},
                {"$sort": {"trade_date": -1}},
                {"$group": {"_id": "$ts_code", "latest": {"$first": "$$ROOT"}}},
                {"$project": {"_id": 0, "ts_code": "$_id", "quote": "$latest"}},
            ]
            results = await self.db["daily_quotes"].aggregate(pipeline).to_list(None)
            for r in results:
                q = r["quote"]
                q.pop("_id", None)
                quotes.append(q)

        return {
            "date": datetime.now().strftime("%Y%m%d"),
            "holdings_count": len(ts_codes),
            "unresolved_events": len(events),
            "unacknowledged_alerts": len(alerts),
            "events": events[:5],
            "alerts": alerts[:5],
            "quotes": quotes,
        }
