import asyncio
import math
import pandas as pd
from datetime import datetime, timedelta
from app.core.database import get_job_db
from pymongo import UpdateOne


def _safe_val(val):
    if val is None:
        return None
    if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
        return None
    try:
        v = float(val)
        if math.isnan(v) or math.isinf(v):
            return None
        return round(v, 4)
    except (ValueError, TypeError):
        return None


def _ts_code_from_symbol(symbol: str) -> str:
    code = str(symbol).zfill(6)
    suffix = ".SH" if code.startswith(("6", "5", "9")) else ".SZ"
    return f"{code}{suffix}"


async def _sync_individual_fund_flow(db, codes):
    import akshare as ak
    ops = []
    total = len(codes)
    for idx, ts_code in enumerate(codes):
        symbol = ts_code.split(".")[0]
        try:
            df = await asyncio.to_thread(
                ak.stock_individual_fund_flow,
                stock=symbol,
                market="sh" if symbol.startswith(("6", "5", "9")) else "sz",
            )
            if df is None or df.empty:
                continue
            df = df.sort_values(df.columns[0], ascending=False).head(1)
            row = df.iloc[0]
            col_date = df.columns[0]
            trade_date = str(row.get(col_date, "")).replace("-", "")
            if not trade_date:
                continue
            doc = {
                "ts_code": ts_code,
                "trade_date": trade_date,
                "main_net_buy": _safe_val(row.get("主力净流入-净额", row.get("main_net_buy"))),
                "big_net_buy": _safe_val(row.get("超大单净流入-净额", row.get("big_net_buy"))),
                "industry": None,
                "sector_net_amount": None,
            }
            ops.append(UpdateOne(
                {"ts_code": ts_code, "trade_date": trade_date},
                {"$set": doc},
                upsert=True,
            ))
            if len(ops) >= 500:
                await db["capital_flow"].bulk_write(ops, ordered=False)
                ops = []
        except Exception as e:
            print(f"  {ts_code} 资金流向同步失败: {e}")
        if (idx + 1) % 100 == 0:
            print(f"  已处理 {idx + 1}/{total}")
    if ops:
        await db["capital_flow"].bulk_write(ops, ordered=False)


async def _sync_north_flow(db):
    import akshare as ak
    try:
        df = await asyncio.to_thread(ak.stock_hsgt_north_net_flow_in_em)
        if df is None or df.empty:
            return
        df = df.sort_values(df.columns[0], ascending=False).head(1)
        row = df.iloc[0]
        col_date = df.columns[0]
        trade_date = str(row.get(col_date, "")).replace("-", "")
        if not trade_date:
            return
        doc = {
            "ts_code": "NORTH_FLOW",
            "trade_date": trade_date,
            "north_holding_change": _safe_val(row.get("当日净流入", row.get("north_holding_change"))),
        }
        await db["capital_flow"].update_one(
            {"ts_code": "NORTH_FLOW", "trade_date": trade_date},
            {"$set": doc},
            upsert=True,
        )
        print(f"  北向资金数据已同步: {trade_date}")
    except Exception as e:
        print(f"  北向资金同步失败: {e}")


async def run():
    db, client = await get_job_db()
    try:
        codes = await db["stocks"].distinct("ts_code", {"delist_date": None})
        total = len(codes)
        print(f"开始同步 {total} 只股票的资金流向数据")

        await _sync_individual_fund_flow(db, codes)
        await _sync_north_flow(db)
    finally:
        client.close()
    print("✅ 资金流向数据同步完成")


if __name__ == "__main__":
    asyncio.run(run())
