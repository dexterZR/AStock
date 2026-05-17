from typing import List, Optional, Dict
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime


class PortfolioService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def get_holdings(self) -> List[Dict]:
        pipeline = [
            {"$group": {
                "_id": "$ts_code",
                "name": {"$first": "$name"},
                "total_shares": {
                    "$sum": {"$cond": [{"$eq": ["$action", "buy"]}, "$shares", {"$multiply": ["$shares", -1]}]}
                },
                "total_cost": {
                    "$sum": {"$cond": [{"$eq": ["$action", "buy"]}, {"$multiply": ["$price", "$shares"]}, 0]}
                },
                "buy_shares": {
                    "$sum": {"$cond": [{"$eq": ["$action", "buy"]}, "$shares", 0]}
                },
                "first_buy": {"$min": "$trade_date"},
                "last_trade": {"$max": "$trade_date"},
            }},
            {"$match": {"total_shares": {"$gt": 0}}},
        ]
        holdings = await self.db["trades"].aggregate(pipeline).to_list(None)

        if not holdings:
            return []

        ts_codes = [h["_id"] for h in holdings]

        # 批量查最新行情（N+1 → 1次）
        quote_pipeline = [
            {"$match": {"ts_code": {"$in": ts_codes}, "adjust_flag": "none"}},
            {"$sort": {"trade_date": -1}},
            {"$group": {"_id": "$ts_code", "latest": {"$first": "$$ROOT"}}},
        ]
        quote_results = await self.db["daily_quotes"].aggregate(quote_pipeline).to_list(None)
        quote_map = {r["_id"]: r["latest"] for r in quote_results}
        for v in quote_map.values():
            v.pop("_id", None)

        # 批量查未解决事件（N+1 → 1次）
        event_cursor = self.db["stock_events"].find(
            {"ts_code": {"$in": ts_codes}, "is_resolved": False, "severity": {"$in": ["warning", "critical"]}}
        )
        all_events = await event_cursor.to_list(None)
        event_map: dict = {}
        for e in all_events:
            event_map.setdefault(e["ts_code"], []).append(e)

        for h in holdings:
            ts_code = h["_id"]
            latest = quote_map.get(ts_code)
            events = event_map.get(ts_code, [])

            avg_cost = h["total_cost"] / h["buy_shares"] if h["buy_shares"] > 0 else 0
            latest_price = latest["close"] if latest else 0
            market_value = latest_price * h["total_shares"]
            remaining_cost = avg_cost * h["total_shares"]
            unrealized_pnl = market_value - remaining_cost
            unrealized_pct = (unrealized_pnl / remaining_cost * 100) if remaining_cost > 0 else 0

            risk_level = "normal"
            if events:
                has_critical = any(e["severity"] == "critical" for e in events)
                risk_level = "critical" if has_critical else "high"

            h.update({
                "ts_code": ts_code,
                "avg_cost": round(avg_cost, 3),
                "latest_price": latest_price,
                "market_value": round(market_value, 2),
                "unrealized_pnl": round(unrealized_pnl, 2),
                "unrealized_pnl_pct": round(unrealized_pct, 2),
                "risk_level": risk_level,
                "warning_events": [e["title"] for e in events[:3]],
            })

        return holdings

    async def add_trade(self, trade: dict) -> str:
        trade["total_amount"] = trade["price"] * trade["shares"]
        result = await self.db["trades"].insert_one(trade)
        return str(result.inserted_id)

    async def get_trades(self, ts_code: Optional[str] = None) -> List[Dict]:
        query = {"ts_code": ts_code} if ts_code else {}
        cursor = self.db["trades"].find(query).sort("trade_date", -1)
        return await cursor.to_list(None)

    async def add_decision_log(self, log: dict) -> str:
        result = await self.db["decision_logs"].insert_one(log)
        return str(result.inserted_id)

    async def get_decision_logs(self, ts_code: Optional[str] = None) -> List[Dict]:
        query = {"ts_code": ts_code} if ts_code else {}
        cursor = self.db["decision_logs"].find(query).sort("created_at", -1)
        return await cursor.to_list(None)

    async def review_decision(self, log_id: str, result: dict):
        from bson import ObjectId
        await self.db["decision_logs"].update_one(
            {"_id": ObjectId(log_id)},
            {"$set": {
                "post_result_pnl": result.get("pnl"),
                "post_result_pct": result.get("pnl_pct"),
                "attribution": result.get("attribution"),
                "lessons": result.get("lessons"),
                "reviewed_at": datetime.now().isoformat(),
            }}
        )

    async def get_trade_stats(self) -> Dict:
        trades = await self.db["trades"].find().to_list(None)
        total_trades = len(trades)
        buy_trades = [t for t in trades if t["action"] == "buy"]
        sell_trades = [t for t in trades if t["action"] == "sell"]

        return {
            "total_trades": total_trades,
            "buy_count": len(buy_trades),
            "sell_count": len(sell_trades),
            "avg_buy_price": sum(t["price"] for t in buy_trades) / len(buy_trades) if buy_trades else 0,
        }
