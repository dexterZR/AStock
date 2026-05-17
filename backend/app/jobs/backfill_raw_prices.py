import asyncio
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import UpdateOne
from app.core.config import settings


async def backfill_raw_prices():
    client = AsyncIOMotorClient(settings.MONGO_URI)
    db = client[settings.MONGO_DB]
    col = db["daily_quotes"]

    remaining = await col.count_documents({
        "adjust_flag": "none",
        "close_raw": {"$exists": False},
    })
    if remaining == 0:
        print("所有记录已有非复权价格，无需回填")
        client.close()
        return

    print(f"共有 {remaining} 条记录缺少非复权价格")

    pipeline = [
        {"$match": {"adjust_flag": "none", "close_raw": {"$exists": False}}},
        {"$sort": {"trade_date": -1}},
        {"$group": {
            "_id": "$trade_date",
            "count": {"$sum": 1},
        }},
        {"$sort": {"_id": -1}},
    ]
    date_groups = await col.aggregate(pipeline).to_list(length=None)
    print(f"涉及 {len(date_groups)} 个交易日")

    if not settings.TUSHARE_TOKEN:
        print("❌ 未配置 TUSHARE_TOKEN，无法使用批量回填")
        print("请在 .env 中配置 TUSHARE_TOKEN 后重试")
        client.close()
        return

    import tushare as ts
    ts.set_token(settings.TUSHARE_TOKEN)
    pro = ts.pro_api()

    total_updated = 0

    for dg in date_groups[:30]:
        trade_date = dg["_id"]
        count = dg["count"]
        print(f"\n📅 回填 {trade_date} ({count} 条)")

        try:
            df = await asyncio.to_thread(pro.daily, trade_date=trade_date)
            if df is None or len(df) == 0:
                print(f"  {trade_date}: Tushare 无数据")
                continue

            raw_map = {}
            for _, row in df.iterrows():
                ts_code = row.get("ts_code", "")
                raw_map[ts_code] = {
                    "open_raw": float(row.get("open", 0) or 0),
                    "high_raw": float(row.get("high", 0) or 0),
                    "low_raw": float(row.get("low", 0) or 0),
                    "close_raw": float(row.get("close", 0) or 0),
                }

            ops = []
            for ts_code, raw_prices in raw_map.items():
                if raw_prices["close_raw"] > 0:
                    ops.append(UpdateOne(
                        {"ts_code": ts_code, "trade_date": trade_date, "adjust_flag": "none"},
                        {"$set": raw_prices},
                    ))

            if ops:
                result = await col.bulk_write(ops, ordered=False)
                total_updated += result.modified_count
                print(f"  {trade_date}: 更新 {result.modified_count}/{len(ops)} 条")

            await asyncio.sleep(0.5)

        except Exception as e:
            print(f"  {trade_date}: 失败 {e}")
            await asyncio.sleep(1)

    remaining = await col.count_documents({
        "adjust_flag": "none",
        "close_raw": {"$exists": False},
    })
    total_with_raw = await col.count_documents({
        "adjust_flag": "none",
        "close_raw": {"$exists": True},
    })
    print(f"\n✅ 回填完成: {total_updated} 条已更新, {total_with_raw} 条有非复权价, {remaining} 条仍缺失")
    client.close()


if __name__ == "__main__":
    asyncio.run(backfill_raw_prices())
