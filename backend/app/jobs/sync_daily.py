import asyncio
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.database import get_job_db
from app.infrastructure.tushare_client import data_client
from app.repos.quote_repo import QuoteRepo
from app.repos.stock_repo import StockRepo


async def _get_latest_trade_date() -> str:
    try:
        import tushare as ts
        from app.core.config import settings
        ts.set_token(settings.TUSHARE_TOKEN)
        pro = ts.pro_api()
        today = datetime.now().strftime("%Y%m%d")
        df = pro.trade_cal(exchange='SSE', is_open='1', start_date=today, end_date=today)
        if df is not None and len(df) > 0:
            return str(df.iloc[0]["cal_date"])
        df = pro.trade_cal(exchange='SSE', is_open='1', start_date='20260101', end_date=today)
        if df is not None and len(df) > 0:
            return str(df.iloc[-1]["cal_date"])
    except Exception as e:
        print(f"  获取交易日历失败: {e}")
    return (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")


async def sync_daily_quotes(trade_date: str = None):
    if trade_date is None:
        trade_date = await _get_latest_trade_date()

    if not trade_date:
        print("⚠️ 无法确定交易日，跳过同步")
        return

    db, client = await get_job_db()
    try:
        stocks_df = data_client.get_stock_list()
        if stocks_df is not None and len(stocks_df) > 0:
            stocks = []
            for _, row in stocks_df.iterrows():
                code = str(row.get("code", "")).zfill(6)
                name = str(row.get("name", "")).replace(" ", "")
                if not code:
                    continue
                if code.startswith(("4", "8", "9")):
                    continue
                suffix = ".SH" if code.startswith(("6", "5")) else ".SZ"
                stocks.append({
                    "ts_code": f"{code}{suffix}",
                    "symbol": code,
                    "name": name,
                    "market": "主板",
                    "list_date": "",
                    "delist_date": None,
                    "is_st": "ST" in name,
                    "total_cap": 0,
                    "float_cap": 0,
                })
            stock_repo = StockRepo(db)
            await stock_repo.bulk_upsert(stocks)
            print(f"同步了 {len(stocks)} 只股票基础信息")

        quote_repo = QuoteRepo(db)
        total_written = 0

        try:
            import tushare as ts
            from app.core.config import settings
            ts.set_token(settings.TUSHARE_TOKEN)
            pro = ts.pro_api()

            df = pro.daily(trade_date=trade_date)
            if df is not None and len(df) > 0:
                records = []
                for _, row in df.iterrows():
                    ts_code = row.get("ts_code", "")
                    if ts_code.endswith(".BJ"):
                        continue
                    pct = row.get("pct_chg", 0)
                    if pct is None:
                        pct = 0
                    records.append({
                        "ts_code": row.get("ts_code", ""),
                        "trade_date": str(row.get("trade_date", "")),
                        "open": float(row.get("open", 0) or 0),
                        "high": float(row.get("high", 0) or 0),
                        "low": float(row.get("low", 0) or 0),
                        "close": float(row.get("close", 0) or 0),
                        "volume": int(float(row.get("vol", 0) or 0)),
                        "amount": float(row.get("amount", 0) or 0),
                        "pct_change": float(pct),
                        "is_trading": True,
                        "adjust_flag": "none",
                    })
                count = await quote_repo.bulk_upsert(records)
                total_written += count
                print(f"  Tushare全量: {trade_date} 写入 {count} 条 (共{len(records)}条)")
            else:
                print(f"  Tushare: {trade_date} 无数据，尝试AKShare逐只同步...")
                raise Exception("Tushare无数据，回退AKShare")
        except Exception as e:
            print(f"  Tushare全量同步失败({e})，使用AKShare逐只同步...")
            ts_codes_to_sync = []
            cursor = db["stocks"].find({}, {"ts_code": 1, "_id": 0})
            async for doc in cursor:
                tc = doc.get("ts_code", "")
                if tc and not tc.endswith(".BJ"):
                    ts_codes_to_sync.append(tc)

            batch_size = 50
            for i in range(0, len(ts_codes_to_sync), batch_size):
                batch = ts_codes_to_sync[i:i + batch_size]
                tasks = []
                for ts_code in batch:
                    symbol = ts_code[:6]
                    tasks.append(_sync_one_stock(symbol, trade_date, quote_repo))
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for r in results:
                    if isinstance(r, int) and r > 0:
                        total_written += r
                if (i // batch_size + 1) % 20 == 0:
                    print(f"  AKShare进度: {min(i+batch_size, len(ts_codes_to_sync))}/{len(ts_codes_to_sync)}")

        print(f"✅ 日K线同步完成: {trade_date} 共写入 {total_written} 条")
    finally:
        client.close()


async def _sync_one_stock(symbol: str, trade_date: str, quote_repo: QuoteRepo) -> int:
    try:
        df = await data_client.async_get_daily_kline(
            symbol=symbol, start_date=trade_date, end_date=trade_date)
        if df is None or len(df) == 0:
            return 0
        suffix = ".SH" if symbol.startswith(("6", "5")) else ".SZ"
        records = []
        for _, row in df.iterrows():
            records.append({
                "ts_code": f"{symbol}{suffix}",
                "trade_date": str(row.get("日期", row.get("trade_date", ""))).replace("-", ""),
                "open": float(row.get("开盘", row.get("open", 0))),
                "high": float(row.get("最高", row.get("high", 0))),
                "low": float(row.get("最低", row.get("low", 0))),
                "close": float(row.get("收盘", row.get("close", 0))),
                "volume": int(float(row.get("成交量", row.get("vol", row.get("volume", 0))))),
                "amount": float(row.get("成交额", row.get("amount", 0))),
                "turnover_rate": float(row.get("换手率", row.get("turnover_rate", 0) or 0)),
                "pct_change": float(row.get("涨跌幅", row.get("pct_chg", 0) or 0)),
                "is_trading": True,
                "adjust_flag": "none",
            })
        return await quote_repo.bulk_upsert(records)
    except Exception as e:
        print(f"  [AKShare] {symbol} 同步失败 (非致命): {e}")
        return 0


if __name__ == "__main__":
    asyncio.run(sync_daily_quotes())
