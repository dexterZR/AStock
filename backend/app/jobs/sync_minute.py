import asyncio
import akshare as ak
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.database import get_job_db

async def sync_minute_quotes(symbol: str, period: str = "5"):
    db, client = await get_job_db()
    

    try:
        df = ak.stock_zh_a_hist_min_em(symbol=symbol, period=period)
        if df is None or len(df) == 0:
            return

        suffix = ".SH" if symbol.startswith(("6", "5")) else ".SZ"
        ts_code = f"{symbol}{suffix}"
        today = datetime.now().strftime("%Y%m%d")

        records = []
        for _, row in df.iterrows():
            time_str = str(row.get("时间", "")).replace(":", "")
            if len(time_str) < 4:
                continue
            records.append({
                "ts_code": ts_code,
                "period": period,
                "trade_time": f"{today}{time_str}",
                "trade_date": today,
                "open": float(row.get("开盘", 0)),
                "high": float(row.get("最高", 0)),
                "low": float(row.get("最低", 0)),
                "close": float(row.get("收盘", 0)),
                "volume": int(float(row.get("成交量", 0))),
            })

        if records:
            from pymongo import UpdateOne
            ops = [
                UpdateOne(
                    {"ts_code": r["ts_code"], "period": r["period"], "trade_time": r["trade_time"]},
                    {"$set": r},
                    upsert=True,
                )
                for r in records
            ]
            await db["minute_quotes"].bulk_write(ops, ordered=False)
            print(f"{symbol} {period}分钟线同步完成: {len(records)} 条")
    except Exception as e:
        print(f"{symbol} 分钟线同步失败: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(sync_minute_quotes("600519", "5"))
