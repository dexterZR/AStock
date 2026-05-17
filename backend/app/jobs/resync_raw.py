import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import UpdateOne
from app.core.config import settings


async def resync_with_raw():
    client = AsyncIOMotorClient(settings.MONGO_URI)
    db = client[settings.MONGO_DB]
    col = db["daily_quotes"]

    qfq_count = await col.count_documents({"adjust_flag": "qfq"})
    none_count = await col.count_documents({"adjust_flag": "none"})
    print(f"当前 qfq 记录: {qfq_count}, none 记录: {none_count}")

    if not settings.TUSHARE_TOKEN:
        print("❌ 未配置 TUSHARE_TOKEN")
        client.close()
        return

    import tushare as ts
    ts.set_token(settings.TUSHARE_TOKEN)
    pro = ts.pro_api()

    trade_dates = await col.distinct("trade_date", {"adjust_flag": "qfq"})
    trade_dates.sort(reverse=True)
    print(f"需要替换 {len(trade_dates)} 个交易日的 qfq 数据")

    total_updated = 0

    for i, trade_date in enumerate(trade_dates):
        count = await col.count_documents({"adjust_flag": "qfq", "trade_date": trade_date})
        print(f"\n[{i+1}/{len(trade_dates)}] 📅 替换 {trade_date} ({count} 条)")

        try:
            df = await asyncio.to_thread(pro.daily, trade_date=trade_date)
            if df is None or len(df) == 0:
                print(f"  {trade_date}: Tushare 无数据")
                continue

            ops = []
            for _, row in df.iterrows():
                ts_code = row.get("ts_code", "")
                close_val = float(row.get("close", 0) or 0)
                if close_val <= 0:
                    continue
                ops.append(UpdateOne(
                    {"ts_code": ts_code, "trade_date": trade_date},
                    {"$set": {
                        "open": float(row.get("open", 0) or 0),
                        "high": float(row.get("high", 0) or 0),
                        "low": float(row.get("low", 0) or 0),
                        "close": close_val,
                        "volume": int(float(row.get("vol", 0) or 0)),
                        "amount": float(row.get("amount", 0) or 0),
                        "pct_change": float(row.get("pct_chg", 0) or 0),
                        "adjust_flag": "none",
                    }},
                    upsert=True,
                ))

            if ops:
                result = await col.bulk_write(ops, ordered=False)
                total_updated += result.modified_count + result.upserted_count
                print(f"  {trade_date}: 更新 {result.modified_count + result.upserted_count}/{len(ops)} 条")

            await asyncio.sleep(0.5)

        except Exception as e:
            print(f"  {trade_date}: 失败 {e}")
            await asyncio.sleep(1)

    qfq_remaining = await col.count_documents({"adjust_flag": "qfq"})
    print(f"\n✅ 替换完成: {total_updated} 条已更新, qfq 剩余: {qfq_remaining}")

    if qfq_remaining > 0:
        print(f"\n🗑️  删除剩余 {qfq_remaining} 条 qfq 数据...")
        await col.delete_many({"adjust_flag": "qfq"})
        print("✅ 已删除")

    none_final = await col.count_documents({"adjust_flag": "none"})
    print(f"最终 none 记录: {none_final}")
    client.close()


if __name__ == "__main__":
    asyncio.run(resync_with_raw())
