from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Dict, Optional
from app.models.screener import ScreenerCondition


class ScreenerRepo:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def screen_with_conditions(self, conditions: List[ScreenerCondition], limit: int = 50) -> List[dict]:
        pipeline = []
        match_signal = {}
        match_fundamental = {}
        match_capital = {}
        match_quote = {}
        match_stock = {}

        for c in conditions:
            if c.category == "technical" or c.category == "pattern":
                if c.op == "eq":
                    match_signal[c.field] = c.value
            elif c.category == "fundamental":
                field_path = c.field
                if c.op == "range":
                    rng = {}
                    if c.min is not None:
                        rng["$gte"] = c.min
                    if c.max is not None:
                        rng["$lte"] = c.max
                    match_fundamental[field_path] = rng
                elif c.op == "gt":
                    match_fundamental[field_path] = {"$gt": c.value}
                elif c.op == "lt":
                    match_fundamental[field_path] = {"$lt": c.value}
                elif c.op == "gte":
                    match_fundamental[field_path] = {"$gte": c.value}
                elif c.op == "lte":
                    match_fundamental[field_path] = {"$lte": c.value}
            elif c.category == "capital":
                field_path = c.field
                if c.op == "range":
                    rng = {}
                    if c.min is not None:
                        rng["$gte"] = c.min
                    if c.max is not None:
                        rng["$lte"] = c.max
                    match_capital[field_path] = rng
                elif c.op == "gt":
                    match_capital[field_path] = {"$gt": c.value}
                elif c.op == "lt":
                    match_capital[field_path] = {"$lt": c.value}
            elif c.category == "quote":
                if c.field == "industry":
                    if c.op == "eq" and c.value:
                        match_stock["industry"] = {"$regex": c.value, "$options": "i"}
                    elif c.op == "in_" and c.values:
                        match_stock["industry"] = {"$in": c.values}
                    elif c.op == "in_" and isinstance(c.value, list):
                        match_stock["industry"] = {"$in": c.value}
                    continue
                field_map = {
                    "price": "quote.close",
                    "pct_change": "quote.pct_change",
                    "turnover_rate": "quote.turnover_rate",
                    "volume": "quote.volume",
                    "amount": "quote.amount",
                }
                field_path = field_map.get(c.field, f"quote.{c.field}")
                if c.op == "range":
                    rng = {}
                    if c.min is not None:
                        rng["$gte"] = c.min
                    if c.max is not None:
                        rng["$lte"] = c.max
                    match_quote[field_path] = rng
                elif c.op == "gt":
                    match_quote[field_path] = {"$gt": c.value}
                elif c.op == "lt":
                    match_quote[field_path] = {"$lt": c.value}
                elif c.op == "gte":
                    match_quote[field_path] = {"$gte": c.value}
                elif c.op == "lte":
                    match_quote[field_path] = {"$lte": c.value}
                elif c.op == "eq":
                    match_quote[field_path] = c.value
            elif c.category == "technical" or c.category == "pattern":
                pass

        if match_stock:
            pipeline.append({"$match": match_stock})

        pipeline.append({
            "$lookup": {
                "from": "daily_quotes",
                "let": {"code": "$ts_code"},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$ts_code", "$$code"]}, "adjust_flag": "none"}},
                    {"$sort": {"trade_date": -1}},
                    {"$limit": 2},
                ],
                "as": "quotes",
            }
        })
        pipeline.append({"$set": {
            "quote": {
                "$let": {
                    "vars": {
                        "latest": {"$arrayElemAt": ["$quotes", 0]},
                        "prev": {"$arrayElemAt": ["$quotes", 1]},
                    },
                    "in": {
                        "trade_date": "$$latest.trade_date",
                        "open": "$$latest.open",
                        "high": "$$latest.high",
                        "low": "$$latest.low",
                        "close": "$$latest.close",
                        "volume": {"$ifNull": ["$$latest.volume", "$$latest.vol"]},
                        "amount": "$$latest.amount",
                        "turnover_rate": {"$ifNull": ["$$latest.turnover_rate", {"$ifNull": ["$$prev.turnover_rate", None]}]},
                        "pct_change": "$$latest.pct_change",
                    }
                }
            }
        }})
        pipeline.append({"$unset": "quotes"})
        pipeline.append({"$unwind": {"path": "$quote", "preserveNullAndEmptyArrays": True}})

        pipeline.append({
            "$lookup": {
                "from": "screener_signals",
                "let": {"code": "$ts_code"},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$ts_code", "$$code"]}}},
                    {"$sort": {"trade_date": -1}},
                    {"$limit": 1},
                    {"$project": {"_id": 0}},
                ],
                "as": "signal",
            }
        })
        pipeline.append({"$unwind": {"path": "$signal", "preserveNullAndEmptyArrays": True}})

        pipeline.append({
            "$lookup": {
                "from": "fundamentals",
                "let": {"code": "$ts_code"},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$ts_code", "$$code"]}}},
                    {"$sort": {"trade_date": -1}},
                    {"$limit": 2},
                ],
                "as": "fundamentals_arr",
            }
        })
        pipeline.append({"$set": {
            "fundamental": {
                "$let": {
                    "vars": {
                        "latest": {"$arrayElemAt": ["$fundamentals_arr", 0]},
                        "prev": {"$arrayElemAt": ["$fundamentals_arr", 1]},
                    },
                    "in": {
                        "pe": {"$ifNull": ["$$latest.pe", {"$ifNull": ["$$prev.pe", None]}]},
                        "pb": {"$ifNull": ["$$latest.pb", {"$ifNull": ["$$prev.pb", None]}]},
                        "roe": {"$ifNull": ["$$latest.roe", {"$ifNull": ["$$prev.roe", None]}]},
                        "total_mv": {"$ifNull": ["$$latest.total_mv", {"$ifNull": ["$$prev.total_mv", None]}]},
                        "circ_mv": {"$ifNull": ["$$latest.circ_mv", {"$ifNull": ["$$prev.circ_mv", None]}]},
                        "dividend_yield": {"$ifNull": ["$$latest.dividend_yield", {"$ifNull": ["$$prev.dividend_yield", None]}]},
                    }
                }
            }
        }})
        pipeline.append({"$unset": "fundamentals_arr"})
        pipeline.append({"$unwind": {"path": "$fundamental", "preserveNullAndEmptyArrays": True}})

        pipeline.append({
            "$lookup": {
                "from": "capital_flow",
                "let": {"code": "$ts_code"},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$ts_code", "$$code"]}}},
                    {"$sort": {"trade_date": -1}},
                    {"$limit": 1},
                    {"$project": {"_id": 0}},
                ],
                "as": "capital",
            }
        })
        pipeline.append({"$unwind": {"path": "$capital", "preserveNullAndEmptyArrays": True}})

        match_final = {}
        if match_signal:
            for k, v in match_signal.items():
                match_final[f"signal.{k}"] = v
        if match_fundamental:
            for k, v in match_fundamental.items():
                match_final[f"fundamental.{k}"] = v
        if match_capital:
            for k, v in match_capital.items():
                match_final[f"capital.{k}"] = v
        if match_quote:
            match_final.update(match_quote)

        if match_final:
            pipeline.append({"$match": match_final})

        pipeline.append({"$limit": limit})
        pipeline.append({"$project": {
            "_id": 0,
            "ts_code": 1,
            "name": 1,
            "industry": 1,
            "market": 1,
            "close": {"$ifNull": ["$quote.close", None]},
            "pct_change": {"$ifNull": ["$quote.pct_change", None]},
            "turnover_rate": {"$ifNull": ["$quote.turnover_rate", None]},
            "volume": {"$ifNull": ["$quote.volume", None]},
            "amount": {"$ifNull": ["$quote.amount", None]},
            "pe": {"$ifNull": ["$fundamental.pe", None]},
            "pb": {"$ifNull": ["$fundamental.pb", None]},
            "roe": {"$ifNull": ["$fundamental.roe", None]},
            "total_mv": {"$ifNull": ["$fundamental.total_mv", None]},
            "main_net_buy": {"$ifNull": ["$capital.main_net_buy", None]},
            "north_holding_change": {"$ifNull": ["$capital.north_holding_change", None]},
            "signals": "$signal",
        }})

        cursor = self.db["stocks"].aggregate(pipeline, allowDiskUse=True, maxTimeMS=15000)
        return await cursor.to_list(length=limit)

    async def get_industries(self) -> List[str]:
        cursor = self.db["stocks"].distinct("industry")
        return await cursor if hasattr(cursor, '__await__') else cursor

    async def get_signals_for_codes(self, ts_codes: List[str]) -> List[dict]:
        cursor = self.db["screener_signals"].find(
            {"ts_code": {"$in": ts_codes}},
            {"_id": 0}
        ).sort("trade_date", -1)
        return await cursor.to_list(length=len(ts_codes))
