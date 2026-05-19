import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from app.core.database import get_job_db
from pymongo import UpdateOne


def compute_signals_from_latest(quotes_df: pd.DataFrame, latest_indicators: dict) -> dict:
    q = quotes_df.copy().sort_values("trade_date").reset_index(drop=True)
    n = len(q)
    if n < 20:
        return None

    close = q["close"].values
    volume = q["volume"].values
    pct_change = q["pct_change"].values if "pct_change" in q.columns else np.zeros(n)

    i = n - 1

    ma5 = latest_indicators.get("ma_5")
    ma10 = latest_indicators.get("ma_10")
    ma20 = latest_indicators.get("ma_20")
    ma60 = latest_indicators.get("ma_60")
    macd_bar = latest_indicators.get("macd_bar")
    kdj_k = latest_indicators.get("kdj_k")
    kdj_d = latest_indicators.get("kdj_d")
    rsi6 = latest_indicators.get("rsi_6")
    boll_upper = latest_indicators.get("boll_upper")
    boll_lower = latest_indicators.get("boll_lower")

    prev_close = close[i - 1] if i >= 1 else close[i]
    prev_ma5 = None
    prev_ma10 = None
    prev_ma20 = None
    prev_macd_bar = None
    prev_kdj_k = None
    prev_kdj_d = None

    if n >= 2:
        prev_close_2 = close[i - 2] if i >= 2 else close[i - 1]
        if ma5 and ma10:
            prev_ma5 = (ma5 * 5 - close[i] + prev_close) / 5 if close[i] != prev_close else ma5
            prev_ma10 = (ma10 * 10 - close[i] + prev_close) / 10 if close[i] != prev_close else ma10
        if ma5 and ma20:
            prev_ma20 = (ma20 * 20 - close[i] + prev_close) / 20 if close[i] != prev_close else ma20
        if macd_bar is not None:
            prev_macd_bar = macd_bar * 0.7
        if kdj_k is not None and kdj_d is not None:
            prev_kdj_k = kdj_k - 1
            prev_kdj_d = kdj_d - 0.5

    def _safe_gt(a, b):
        return a is not None and b is not None and a > b

    def _safe_lte(a, b):
        return a is not None and b is not None and a <= b

    ma5_cross_ma10 = _safe_gt(ma5, ma10) and _safe_lte(prev_ma5, prev_ma10) if prev_ma5 is not None else False
    ma5_cross_ma20 = _safe_gt(ma5, ma20) and _safe_lte(prev_ma5, prev_ma20) if prev_ma5 is not None else False
    ma10_cross_ma20 = _safe_gt(ma10, ma20) and _safe_lte(prev_ma10, prev_ma20) if prev_ma10 is not None else False

    macd_cross = (macd_bar is not None and macd_bar > 0 and prev_macd_bar is not None and prev_macd_bar <= 0)

    kdj_cross = _safe_gt(kdj_k, kdj_d) and _safe_lte(prev_kdj_k, prev_kdj_d) if prev_kdj_k is not None else False

    rsi_oversold = rsi6 is not None and rsi6 < 30
    rsi_overbought = rsi6 is not None and rsi6 > 70

    boll_breakout_up = boll_upper is not None and close[i] > boll_upper
    boll_breakout_down = boll_lower is not None and close[i] < boll_lower

    ma_bullish = (
        ma5 is not None and ma10 is not None and ma20 is not None and ma60 is not None
        and ma5 > ma10 > ma20 > ma60
    )
    ma_bearish = (
        ma5 is not None and ma10 is not None and ma20 is not None and ma60 is not None
        and ma5 < ma10 < ma20 < ma60
    )

    vol_ma5 = np.mean(volume[max(0, i - 5):i]) if i >= 5 else np.nan
    volume_surge = (not np.isnan(vol_ma5) and vol_ma5 > 0 and volume[i] > vol_ma5 * 2)
    volume_shrink = (not np.isnan(vol_ma5) and vol_ma5 > 0 and volume[i] < vol_ma5 * 0.5)

    high_20 = np.max(close[max(0, i - 19):i + 1])
    breakout_20d_high = close[i] >= high_20

    high_60 = np.max(close[max(0, i - 59):i + 1])
    breakout_60d_high = close[i] >= high_60

    low_20 = np.min(close[max(0, i - 19):i + 1])
    drop_20d_low = close[i] <= low_20

    ret_5d = (close[i] / close[max(0, i - 5)] - 1) if close[max(0, i - 5)] != 0 else 0
    has_big_drop = False
    for j in range(max(1, i - 9), i + 1):
        if pct_change[j] < -3:
            has_big_drop = True
            break
    v_shape_recovery = ret_5d > 0.08 and has_big_drop

    recent_10_high = np.max(close[max(0, i - 9):i + 1])
    recent_10_low = np.min(close[max(0, i - 9):i + 1])
    amplitude = (recent_10_high - recent_10_low) / recent_10_low if recent_10_low != 0 else 1
    consolidation = amplitude < 0.05 and volume_shrink

    continuous_up_3d = all(pct_change[j] > 0 for j in range(max(0, i - 2), i + 1)) if i >= 2 else False

    continuous_volume_3d = (
        i >= 5
        and not np.isnan(vol_ma5)
        and vol_ma5 > 0
        and all(volume[j] > vol_ma5 for j in range(max(0, i - 2), i + 1))
    )

    return {
        "ma5_cross_ma10": bool(ma5_cross_ma10),
        "ma5_cross_ma20": bool(ma5_cross_ma20),
        "ma10_cross_ma20": bool(ma10_cross_ma20),
        "macd_cross": bool(macd_cross),
        "kdj_cross": bool(kdj_cross),
        "rsi_oversold": bool(rsi_oversold),
        "rsi_overbought": bool(rsi_overbought),
        "boll_breakout_up": bool(boll_breakout_up),
        "boll_breakout_down": bool(boll_breakout_down),
        "ma_bullish": bool(ma_bullish),
        "ma_bearish": bool(ma_bearish),
        "volume_surge": bool(volume_surge),
        "volume_shrink": bool(volume_shrink),
        "breakout_20d_high": bool(breakout_20d_high),
        "breakout_60d_high": bool(breakout_60d_high),
        "drop_20d_low": bool(drop_20d_low),
        "v_shape_recovery": bool(v_shape_recovery),
        "consolidation": bool(consolidation),
        "continuous_up_3d": bool(continuous_up_3d),
        "continuous_volume_3d": bool(continuous_volume_3d),
    }


async def _process_batch(db, batch_codes):
    quotes_pipeline = [
        {"$match": {"ts_code": {"$in": batch_codes}, "adjust_flag": "none"}},
        {"$sort": {"trade_date": 1}},
        {"$group": {
            "_id": "$ts_code",
            "quotes": {"$push": {
                "trade_date": "$trade_date", "close": "$close",
                "volume": "$volume", "pct_change": "$pct_change",
            }},
        }},
    ]
    quotes_groups = await db["daily_quotes"].aggregate(quotes_pipeline).to_list(None)
    quotes_map = {g["_id"]: g["quotes"] for g in quotes_groups}

    ind_docs = await db["indicators"].find(
        {"ts_code": {"$in": batch_codes}},
        {"_id": 0},
    ).to_list(None)
    ind_map = {}
    for doc in ind_docs:
        tc = doc.get("ts_code", "")
        existing = ind_map.get(tc)
        if existing is None or doc.get("trade_date", "") > existing.get("trade_date", ""):
            ind_map[tc] = doc

    all_ops = []
    for ts_code in batch_codes:
        quotes = quotes_map.get(ts_code)
        indicators = ind_map.get(ts_code)
        if not quotes or not indicators:
            continue
        if len(quotes) < 20:
            continue

        quotes_df = pd.DataFrame(quotes)

        signals = compute_signals_from_latest(quotes_df, indicators)
        if signals is None:
            continue

        trade_date = str(quotes_df.iloc[-1]["trade_date"])
        doc = {"ts_code": ts_code, "trade_date": trade_date, **signals}
        all_ops.append(UpdateOne(
            {"ts_code": ts_code, "trade_date": trade_date},
            {"$set": doc},
            upsert=True,
        ))

    if all_ops:
        await db["screener_signals"].bulk_write(all_ops, ordered=False)
    return len(all_ops)


async def run():
    db, client = await get_job_db()
    try:
        codes = await db["stocks"].distinct("ts_code", {"delist_date": None})
        total = len(codes)
        print(f"开始计算 {total} 只股票的筛选信号(批量模式)")

        batch_size = 200
        total_written = 0
        for i in range(0, len(codes), batch_size):
            batch = codes[i:i + batch_size]
            try:
                written = await _process_batch(db, batch)
                total_written += written
            except Exception as e:
                print(f"  批次 {i//batch_size + 1} 失败: {e}")
            if (i // batch_size + 1) % 5 == 0 or i + batch_size >= len(codes):
                print(f"  已处理 {min(i + batch_size, total)}/{total}, 写入 {total_written} 条")
    finally:
        client.close()
    print(f"✅ 筛选信号计算完成, 共写入 {total_written} 条")


if __name__ == "__main__":
    asyncio.run(run())
