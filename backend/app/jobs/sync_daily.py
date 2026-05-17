import asyncio
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.database import get_job_db
from app.infrastructure.tushare_client import data_client
from app.repos.quote_repo import QuoteRepo
from app.repos.stock_repo import StockRepo


async def sync_daily_quotes(trade_date: str = None):
    if trade_date is None:
        trade_date = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")

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
                suffix = ".SH" if code.startswith(("6", "5", "9")) else ".SZ"
                stocks.append({
                    "ts_code": f"{code}{suffix}",
                    "symbol": code,
                    "name": name,
                    "industry": "",
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

        symbols = ["000001", "600519", "002594", "300750", "600036"]
        quote_repo = QuoteRepo(db)
        for symbol in symbols:
            try:
                df = data_client.get_daily_kline(
                    symbol=symbol, start_date=trade_date, end_date=trade_date)
                if df is None or len(df) == 0:
                    continue
                suffix = ".SH" if symbol.startswith(("6", "5", "9")) else ".SZ"
                records = []
                for _, row in df.iterrows():
                    records.append({
                        "ts_code": f"{symbol}{suffix}",
                        "trade_date": str(row.get("日期", row.get("trade_date", ""))).replace("-", ""),
                        "open": float(row.get("开盘", row.get("open", 0))),
                        "high": float(row.get("最高", row.get("high", 0))),
                        "low": float(row.get("最低", row.get("low", 0))),
                        "close": float(row.get("收盘", row.get("close", 0))),
                        "volume": int(float(row.get("成交量", row.get("volume", 0)))),
                        "amount": float(row.get("成交额", row.get("amount", 0))),
                        "turnover_rate": float(row.get("换手率", row.get("turnover_rate", 0))),
                        "pct_change": float(row.get("涨跌幅", row.get("pct_chg", 0))),
                        "is_trading": True,
                        "adjust_flag": "none",
                    })
                count = await quote_repo.bulk_upsert(records)
                print(f"  {symbol}: 写入 {count} 条")
            except Exception as e:
                print(f"  {symbol}: 同步失败 {e}")
    finally:
        client.close()
    print("✅ 日终同步完成")


if __name__ == "__main__":
    asyncio.run(sync_daily_quotes())
