import asyncio
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.database import get_job_db

async def generate_and_push_daily_brief():
    db, client = await get_job_db()
    try:
        pipeline = [{"$group": {"_id": "$ts_code", "name": {"$first": "$name"}}}]
        holdings = await db["trades"].aggregate(pipeline).to_list(None)
        ts_codes = [h["_id"] for h in holdings]
        if not ts_codes:
            print("暂无持仓")
            return
        events = await db["stock_events"].find({
            "ts_code": {"$in": ts_codes}, "is_resolved": False,
            "severity": {"$in": ["warning", "critical"]},
        }).sort("event_date", -1).to_list(None)
        alerts = await db["risk_alerts"].find({
            "ts_code": {"$in": ts_codes}, "is_acknowledged": False,
        }).sort("triggered_at", -1).to_list(None)
        quotes = []
        if ts_codes:
            quote_pipeline = [
                {"$match": {"ts_code": {"$in": ts_codes}, "adjust_flag": "none"}},
                {"$sort": {"trade_date": -1}},
                {"$group": {"_id": "$ts_code", "latest": {"$first": "$$ROOT"}}},
            ]
            quote_results = await db["daily_quotes"].aggregate(quote_pipeline).to_list(None)
            quote_map = {r["_id"]: r["latest"] for r in quote_results}
            for v in quote_map.values():
                v.pop("_id", None)
            all_trades = await db["trades"].find({"action": "buy"}).to_list(None)
            trade_map = {}
            for t in all_trades:
                trade_map.setdefault(t["ts_code"], []).append(t)
            for code in ts_codes:
                q = quote_map.get(code)
                if not q:
                    continue
                trades = trade_map.get(code, [])
                total_cost = sum(t["price"] * t["shares"] for t in trades)
                total_shares = sum(t["shares"] for t in trades)
                avg_cost = total_cost / total_shares if total_shares > 0 else 0
                q["avg_cost"] = round(avg_cost, 2)
                q["unrealized_pct"] = round((q["close"] - avg_cost) / avg_cost * 100, 2)
                quotes.append(q)
        date_str = datetime.now().strftime("%Y-%m-%d")
        lines = [f"📊 持仓风险简报 ({date_str})", ""]
        for q in quotes:
            emoji = "🟢" if q["unrealized_pct"] >= 0 else "🔴"
            lines.append(f"{emoji} {q['ts_code']} {q.get('name', '')}")
            lines.append(f"  现价: {q['close']:.2f} | 成本: {q['avg_cost']:.2f} | 浮盈: {q['unrealized_pct']:+.2f}%")
            stock_events = [e for e in events if e["ts_code"] == q["ts_code"]]
            if stock_events:
                lines.append(f"  ⚠️ 未解决事件: {len(stock_events)}条")
                for e in stock_events[:2]:
                    sev = "🔴" if e["severity"] == "critical" else "🟡"
                    lines.append(f"    {sev} [{e['event_type']}] {e['title']}")
            lines.append("")
        if not events and not alerts:
            lines.append("✅ 今日无新增风险事件")
        print("\n".join(lines))
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(generate_and_push_daily_brief())
