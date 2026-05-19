import asyncio
from datetime import datetime
from app.core.database import get_job_db
from pymongo import UpdateOne


async def build_snapshot():
    db, client = await get_job_db()
    try:
        latest_quote = await db["daily_quotes"].find_one(
            {"adjust_flag": "none"},
            {"trade_date": 1},
            sort=[("trade_date", -1)],
        )
        if not latest_quote:
            print("  快照: 无行情数据，跳过")
            return

        trade_date = latest_quote["trade_date"]
        print(f"  快照: 构建 {trade_date} 的筛选快照...")

        pipeline = [
            {"$match": {"adjust_flag": "none", "trade_date": trade_date}},
            {"$lookup": {
                "from": "stocks",
                "let": {"code": "$ts_code"},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$ts_code", "$$code"]}}},
                    {"$project": {"_id": 0, "name": 1, "industry": 1, "market": 1}},
                    {"$limit": 1},
                ],
                "as": "stock",
            }},
            {"$unwind": {"path": "$stock", "preserveNullAndEmptyArrays": True}},
            {"$lookup": {
                "from": "screener_signals",
                "let": {"code": "$ts_code"},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$ts_code", "$$code"]}}},
                    {"$sort": {"trade_date": -1}},
                    {"$limit": 1},
                    {"$project": {"_id": 0, "ts_code": 0, "trade_date": 0}},
                ],
                "as": "signal",
            }},
            {"$unwind": {"path": "$signal", "preserveNullAndEmptyArrays": True}},
            {"$lookup": {
                "from": "fundamentals",
                "let": {"code": "$ts_code"},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$ts_code", "$$code"]}}},
                    {"$sort": {"trade_date": -1}},
                    {"$limit": 5},
                    {"$project": {"_id": 0}},
                ],
                "as": "fundamentals_arr",
            }},
            {"$set": {
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
                            "total_mv": {
                                "$reduce": {
                                    "input": "$fundamentals_arr",
                                    "initialValue": None,
                                    "in": {"$ifNull": ["$$this.total_mv", "$$value"]},
                                }
                            },
                            "circ_mv": {"$ifNull": ["$$latest.circ_mv", {"$ifNull": ["$$prev.circ_mv", None]}]},
                            "dividend_yield": {"$ifNull": ["$$latest.dividend_yield", {"$ifNull": ["$$prev.dividend_yield", None]}]},
                        }
                    }
                }
            }},
            {"$unset": "fundamentals_arr"},
            {"$project": {
                "_id": 0,
                "ts_code": 1,
                "name": {"$ifNull": ["$stock.name", ""]},
                "industry": {"$ifNull": ["$stock.industry", ""]},
                "market": {"$ifNull": ["$stock.market", ""]},
                "trade_date": 1,
                "close": 1,
                "pct_change": {"$ifNull": ["$pct_change", None]},
                "volume": {"$ifNull": ["$volume", {"$ifNull": ["$vol", None]}]},
                "amount": {"$ifNull": ["$amount", None]},
                "turnover_rate": {"$ifNull": ["$turnover_rate", None]},
                "pe": {"$ifNull": ["$fundamental.pe", None]},
                "pb": {"$ifNull": ["$fundamental.pb", None]},
                "roe": {"$ifNull": ["$fundamental.roe", None]},
                "total_mv": {"$ifNull": ["$fundamental.total_mv", None]},
                "circ_mv": {"$ifNull": ["$fundamental.circ_mv", None]},
                "dividend_yield": {"$ifNull": ["$fundamental.dividend_yield", None]},
                "signals": {"$ifNull": ["$signal", {}]},
            }},
        ]

        docs = await db["daily_quotes"].aggregate(pipeline, allowDiskUse=True).to_list(None)

        if not docs:
            print("  快照: 无数据")
            return

        ops = []
        for doc in docs:
            doc["snapshot_date"] = trade_date
            ops.append(UpdateOne(
                {"ts_code": doc["ts_code"], "snapshot_date": trade_date},
                {"$set": doc},
                upsert=True,
            ))

        if ops:
            await db["screener_snapshot"].bulk_write(ops, ordered=False)

        await db["screener_snapshot"].create_index(
            [("ts_code", 1), ("snapshot_date", -1)],
            unique=True, name="idx_snapshot_code_date",
        )
        await db["screener_snapshot"].create_index(
            [("snapshot_date", -1)],
            name="idx_snapshot_date",
        )

        print(f"  快照: ✅ 写入 {len(docs)} 条 (trade_date={trade_date})")
    finally:
        client.close()


async def build_market_stats():
    db, client = await get_job_db()
    try:
        latest = await db["daily_quotes"].find_one(
            {"adjust_flag": "none"},
            {"trade_date": 1},
            sort=[("trade_date", -1)],
        )
        if not latest:
            return

        trade_date = latest["trade_date"]

        pipeline = [
            {"$match": {"adjust_flag": "none", "trade_date": trade_date}},
            {"$group": {
                "_id": None,
                "total": {"$sum": 1},
                "up": {"$sum": {"$cond": [{"$gt": ["$pct_change", 0]}, 1, 0]}},
                "down": {"$sum": {"$cond": [{"$lt": ["$pct_change", 0]}, 1, 0]}},
                "flat": {"$sum": {"$cond": [{"$eq": ["$pct_change", 0]}, 1, 0]}},
                "limit_up": {"$sum": {"$cond": [{"$gte": ["$pct_change", 9.9]}, 1, 0]}},
                "limit_down": {"$sum": {"$cond": [{"$lte": ["$pct_change", -9.9]}, 1, 0]}},
                "total_amount": {"$sum": "$amount"},
            }},
        ]
        result = await db["daily_quotes"].aggregate(pipeline).to_list(1)

        if result:
            r = result[0]
            stats = {
                "trade_date": trade_date,
                "total_stocks": r["total"],
                "up_count": r["up"],
                "down_count": r["down"],
                "flat_count": r["flat"],
                "limit_up_count": r["limit_up"],
                "limit_down_count": r["limit_down"],
                "turnover_total": round(r["total_amount"] / 1e8, 2),
                "updated_at": datetime.now().isoformat(),
            }
            await db["market_stats"].replace_one(
                {"trade_date": trade_date},
                stats,
                upsert=True,
            )
            print(f"  市场统计: ✅ {trade_date} 涨{r['up']}/跌{r['down']}/平{r['flat']}")

        top_up_pipeline = [
            {"$match": {"adjust_flag": "none", "trade_date": trade_date}},
            {"$sort": {"pct_change": -1}},
            {"$limit": 50},
            {"$lookup": {
                "from": "stocks",
                "let": {"code": "$ts_code"},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$ts_code", "$$code"]}}},
                    {"$project": {"name": 1, "_id": 0}},
                    {"$limit": 1},
                ],
                "as": "stock",
            }},
            {"$unwind": {"path": "$stock", "preserveNullAndEmptyArrays": True}},
            {"$project": {
                "_id": 0, "ts_code": 1,
                "name": {"$ifNull": ["$stock.name", ""]},
                "pct_change": 1, "close": 1, "amount": 1,
            }},
        ]
        top_up = await db["daily_quotes"].aggregate(top_up_pipeline).to_list(50)
        await db["market_top"].replace_one(
            {"type": "up", "trade_date": trade_date},
            {"type": "up", "trade_date": trade_date, "stocks": top_up},
            upsert=True,
        )

        top_down_pipeline = [
            {"$match": {"adjust_flag": "none", "trade_date": trade_date}},
            {"$sort": {"pct_change": 1}},
            {"$limit": 50},
            {"$lookup": {
                "from": "stocks",
                "let": {"code": "$ts_code"},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$ts_code", "$$code"]}}},
                    {"$project": {"name": 1, "_id": 0}},
                    {"$limit": 1},
                ],
                "as": "stock",
            }},
            {"$unwind": {"path": "$stock", "preserveNullAndEmptyArrays": True}},
            {"$project": {
                "_id": 0, "ts_code": 1,
                "name": {"$ifNull": ["$stock.name", ""]},
                "pct_change": 1, "close": 1, "amount": 1,
            }},
        ]
        top_down = await db["daily_quotes"].aggregate(top_down_pipeline).to_list(50)
        await db["market_top"].replace_one(
            {"type": "down", "trade_date": trade_date},
            {"type": "down", "trade_date": trade_date, "stocks": top_down},
            upsert=True,
        )
        print(f"  涨跌榜: ✅ 涨幅前50 + 跌幅前50 已缓存")
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(build_snapshot())
