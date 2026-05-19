import asyncio
import math
from datetime import datetime, timedelta
from app.core.database import get_job_db
from pymongo import UpdateOne


def _safe_val(val, allow_zero=True):
    if val is None:
        return None
    if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
        return None
    try:
        v = float(val)
        if math.isnan(v) or math.isinf(v):
            return None
        if not allow_zero and v == 0:
            return None
        return round(v, 4)
    except (ValueError, TypeError):
        return None


async def _sync_via_tushare(db):
    import tushare as ts
    from app.core.config import settings
    ts.set_token(settings.TUSHARE_TOKEN)
    pro = ts.pro_api()

    trade_date = None
    for days_back in range(1, 10):
        candidate = (datetime.now() - timedelta(days=days_back)).strftime("%Y%m%d")
        try:
            df = await asyncio.to_thread(
                pro.daily_basic,
                trade_date=candidate,
                fields="ts_code,trade_date,close,pe,pb,turnover_rate,dv_ratio,total_mv,circ_mv",
            )
            if df is not None and not df.empty:
                trade_date = candidate
                break
        except Exception:
            continue

    if trade_date is None:
        print("  tushare daily_basic: 最近10天均无数据")
        return False

    df = await asyncio.to_thread(
        pro.daily_basic,
        trade_date=trade_date,
        fields="ts_code,trade_date,close,pe,pb,turnover_rate,dv_ratio,total_mv,circ_mv",
    )
    if df is None or df.empty:
        print("  tushare daily_basic: 返回空数据")
        return False

    print(f"  tushare daily_basic: 获取到 {len(df)} 条数据 (trade_date={trade_date})")

    ops = []
    for _, row in df.iterrows():
        ts_code = str(row.get("ts_code", ""))
        if not ts_code or ts_code.endswith(".BJ"):
            continue
        doc = {
            "ts_code": ts_code,
            "trade_date": str(row.get("trade_date", "")),
            "pe": _safe_val(row.get("pe")),
            "pb": _safe_val(row.get("pb")),
            "roe": None,
            "revenue_growth": None,
            "profit_growth": None,
            "dividend_yield": _safe_val(row.get("dv_ratio")),
            "total_mv": _safe_val(row.get("total_mv"), allow_zero=False),
            "circ_mv": _safe_val(row.get("circ_mv"), allow_zero=False),
        }
        ops.append(UpdateOne(
            {"ts_code": ts_code, "trade_date": doc["trade_date"]},
            {"$set": doc},
            upsert=True,
        ))
        if len(ops) >= 1000:
            await db["fundamentals"].bulk_write(ops, ordered=False)
            ops = []

    if ops:
        await db["fundamentals"].bulk_write(ops, ordered=False)

    tr_count = sum(1 for _, row in df.iterrows() if _safe_val(row.get("turnover_rate")) is not None)
    pe_count = sum(1 for _, row in df.iterrows() if _safe_val(row.get("pe")) is not None)
    pb_count = sum(1 for _, row in df.iterrows() if _safe_val(row.get("pb")) is not None)
    print(f"  tushare 写入完成: PE={pe_count}, PB={pb_count}, turnover_rate={tr_count}")

    await _sync_roe_via_tushare(db, pro)

    return True


async def _sync_roe_via_tushare(db, pro):
    try:
        roe_count = await db["fundamentals"].count_documents({"roe": {"$ne": None}})
        if roe_count > 1000:
            print(f"  ROE数据已存在({roe_count}条), 跳过同步")
            return

        codes = await db["stocks"].distinct("ts_code", {"delist_date": None})
        print(f"  开始同步ROE数据, 共{len(codes)}只股票...")

        batch_size = 50
        total_roe = 0
        total_growth = 0

        for i in range(0, len(codes), batch_size):
            batch = codes[i:i + batch_size]
            tasks = []
            for code in batch:
                tasks.append(_fetch_roe(pro, code))
            results = await asyncio.gather(*tasks, return_exceptions=True)

            ops = []
            for result in results:
                if isinstance(result, Exception) or result is None:
                    continue
                ts_code, roe_val, rev_g, prof_g = result
                update = {}
                if roe_val is not None:
                    update["roe"] = roe_val
                    total_roe += 1
                if rev_g is not None:
                    update["revenue_growth"] = rev_g
                    total_growth += 1
                if prof_g is not None:
                    update["profit_growth"] = prof_g
                if not update:
                    continue
                ops.append(UpdateOne(
                    {"ts_code": ts_code},
                    {"$set": update},
                ))

            if ops:
                await db["fundamentals"].bulk_write(ops, ordered=False)

            if (i + batch_size) % 500 == 0 or i + batch_size >= len(codes):
                print(f"  ROE进度: {min(i + batch_size, len(codes))}/{len(codes)}, ROE={total_roe}, growth={total_growth}")

            await asyncio.sleep(0.3)

        print(f"  ROE同步完成: ROE={total_roe}, revenue_growth={total_growth}")
    except Exception as e:
        print(f"  ROE同步失败: {e}")


async def _fetch_roe(pro, ts_code):
    try:
        df = await asyncio.to_thread(
            pro.fina_indicator,
            ts_code=ts_code,
            fields="ts_code,ann_date,roe,revenue_growth,profit_growth",
        )
        if df is None or df.empty:
            return None
        row = df.iloc[0]
        return (
            ts_code,
            _safe_val(row.get("roe")),
            _safe_val(row.get("revenue_growth")),
            _safe_val(row.get("profit_growth")),
        )
    except Exception:
        return None


async def _sync_via_baidu(db, codes):
    import akshare as ak
    print(f"  通过 stock_zh_valuation_baidu 获取 {len(codes)} 只股票的PE/PB...")
    ops = []
    success = 0
    fail = 0

    for idx, ts_code in enumerate(codes):
        symbol = ts_code.split(".")[0]
        pe_val = None
        pb_val = None
        mv_val = None

        try:
            pe_df = await asyncio.to_thread(ak.stock_zh_valuation_baidu, symbol=symbol, indicator="市盈率(TTM)")
            if pe_df is not None and not pe_df.empty:
                pe_val = _safe_val(pe_df.iloc[-1]["value"])
        except Exception:
            pass

        try:
            pb_df = await asyncio.to_thread(ak.stock_zh_valuation_baidu, symbol=symbol, indicator="市净率")
            if pb_df is not None and not pb_df.empty:
                pb_val = _safe_val(pb_df.iloc[-1]["value"])
        except Exception:
            pass

        try:
            mv_df = await asyncio.to_thread(ak.stock_zh_valuation_baidu, symbol=symbol, indicator="总市值")
            if mv_df is not None and not mv_df.empty:
                v = mv_df.iloc[-1]["value"]
                mv_val = _safe_val(v)
                if mv_val:
                    mv_val = round(mv_val / 100000000, 4)
        except Exception:
            pass

        if pe_val is not None or pb_val is not None:
            doc = {}
            if pe_val is not None:
                doc["pe"] = pe_val
            if pb_val is not None:
                doc["pb"] = pb_val
            if mv_val is not None:
                doc["total_mv"] = mv_val
            doc["trade_date"] = datetime.now().strftime("%Y%m%d")
            ops.append(UpdateOne(
                {"ts_code": ts_code},
                {"$set": doc},
                upsert=True,
            ))
            success += 1
        else:
            fail += 1

        if len(ops) >= 500:
            await db["fundamentals"].bulk_write(ops, ordered=False)
            ops = []

        if (idx + 1) % 500 == 0:
            print(f"  已处理 {idx + 1}/{len(codes)}, success={success}, fail={fail}")

    if ops:
        await db["fundamentals"].bulk_write(ops, ordered=False)

    print(f"  百度估值同步完成: success={success}, fail={fail}")
    return success > 0


async def run():
    db, client = await get_job_db()
    try:
        codes = await db["stocks"].distinct("ts_code", {"delist_date": None})
        total = len(codes)
        print(f"开始同步 {total} 只股票的基本面数据")

        try:
            ok = await _sync_via_tushare(db)
            if not ok:
                raise Exception("tushare 返回空数据")
        except Exception as e:
            print(f"tushare 同步失败: {e}，尝试百度估值...")
            try:
                await _sync_via_baidu(db, codes)
            except Exception as e2:
                print(f"百度估值同步也失败: {e2}")
    finally:
        client.close()
    print("✅ 基本面数据同步完成")


if __name__ == "__main__":
    asyncio.run(run())
