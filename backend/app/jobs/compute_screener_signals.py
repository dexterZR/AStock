import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from app.core.database import get_job_db
from pymongo import UpdateOne


def _safe_float(val):
    if val is None or (isinstance(val, float) and (np.isnan(val) or np.isinf(val))):
        return None
    return round(float(val), 4)


def compute_signals(quotes_df: pd.DataFrame, indicators_df: pd.DataFrame) -> dict:
    q = quotes_df.copy().sort_values("trade_date").reset_index(drop=True)
    ind = indicators_df.copy().sort_values("trade_date").reset_index(drop=True)

    n = len(q)
    if n < 60:
        return None

    close = q["close"].values
    volume = q["volume"].values
    pct_change = q["pct_change"].values if "pct_change" in q.columns else np.zeros(n)

    ma5 = ind["ma_5"].values if "ma_5" in ind.columns else np.full(n, np.nan)
    ma10 = ind["ma_10"].values if "ma_10" in ind.columns else np.full(n, np.nan)
    ma20 = ind["ma_20"].values if "ma_20" in ind.columns else np.full(n, np.nan)
    ma60 = ind["ma_60"].values if "ma_60" in ind.columns else np.full(n, np.nan)
    macd_bar = ind["macd_bar"].values if "macd_bar" in ind.columns else np.full(n, np.nan)
    kdj_k = ind["kdj_k"].values if "kdj_k" in ind.columns else np.full(n, np.nan)
    kdj_d = ind["kdj_d"].values if "kdj_d" in ind.columns else np.full(n, np.nan)
    rsi6 = ind["rsi_6"].values if "rsi_6" in ind.columns else np.full(n, np.nan)
    boll_upper = ind["boll_upper"].values if "boll_upper" in ind.columns else np.full(n, np.nan)
    boll_lower = ind["boll_lower"].values if "boll_lower" in ind.columns else np.full(n, np.nan)

    i = n - 1

    def _cross(curr, prev):
        if np.isnan(curr) or np.isnan(prev):
            return False
        return curr > prev

    ma5_cross_ma10 = _cross(ma5[i], ma10[i]) and not _cross(ma5[i - 1], ma10[i - 1]) if i >= 1 else False
    ma5_cross_ma10 = (ma5[i] > ma10[i] and ma5[i - 1] <= ma10[i - 1]) if (i >= 1 and not np.isnan(ma5[i]) and not np.isnan(ma10[i]) and not np.isnan(ma5[i - 1]) and not np.isnan(ma10[i - 1])) else False

    ma5_cross_ma20 = (ma5[i] > ma20[i] and ma5[i - 1] <= ma20[i - 1]) if (i >= 1 and not np.isnan(ma5[i]) and not np.isnan(ma20[i]) and not np.isnan(ma5[i - 1]) and not np.isnan(ma20[i - 1])) else False

    ma10_cross_ma20 = (ma10[i] > ma20[i] and ma10[i - 1] <= ma20[i - 1]) if (i >= 1 and not np.isnan(ma10[i]) and not np.isnan(ma20[i]) and not np.isnan(ma10[i - 1]) and not np.isnan(ma20[i - 1])) else False

    macd_cross = (macd_bar[i] > 0 and macd_bar[i - 1] <= 0) if (i >= 1 and not np.isnan(macd_bar[i]) and not np.isnan(macd_bar[i - 1])) else False

    kdj_cross = (kdj_k[i] > kdj_d[i] and kdj_k[i - 1] <= kdj_d[i - 1]) if (i >= 1 and not np.isnan(kdj_k[i]) and not np.isnan(kdj_d[i]) and not np.isnan(kdj_k[i - 1]) and not np.isnan(kdj_d[i - 1])) else False

    rsi_oversold = (not np.isnan(rsi6[i]) and rsi6[i] < 30)
    rsi_overbought = (not np.isnan(rsi6[i]) and rsi6[i] > 70)

    boll_breakout_up = (not np.isnan(boll_upper[i]) and close[i] > boll_upper[i])
    boll_breakout_down = (not np.isnan(boll_lower[i]) and close[i] < boll_lower[i])

    ma_bullish = (
        not np.isnan(ma5[i]) and not np.isnan(ma10[i]) and not np.isnan(ma20[i]) and not np.isnan(ma60[i])
        and ma5[i] > ma10[i] > ma20[i] > ma60[i]
    )
    ma_bearish = (
        not np.isnan(ma5[i]) and not np.isnan(ma10[i]) and not np.isnan(ma20[i]) and not np.isnan(ma60[i])
        and ma5[i] < ma10[i] < ma20[i] < ma60[i]
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


async def run():
    db, client = await get_job_db()
    try:
        codes = await db["stocks"].distinct("ts_code", {"delist_date": None})
        total = len(codes)
        print(f"开始计算 {total} 只股票的筛选信号")
        ops = []
        for idx, ts_code in enumerate(codes):
            try:
                cursor_q = db["daily_quotes"].find(
                    {"ts_code": ts_code, "adjust_flag": "none"},
                    {"_id": 0}
                ).sort("trade_date", 1).limit(60)
                quotes_rows = await cursor_q.to_list(length=60)

                cursor_i = db["indicators"].find(
                    {"ts_code": ts_code},
                    {"_id": 0}
                ).sort("trade_date", 1).limit(60)
                ind_rows = await cursor_i.to_list(length=60)

                if len(quotes_rows) < 20 or len(ind_rows) < 20:
                    continue

                quotes_df = pd.DataFrame(quotes_rows)
                ind_df = pd.DataFrame(ind_rows)

                signals = compute_signals(quotes_df, ind_df)
                if signals is None:
                    continue

                trade_date = str(quotes_df.iloc[-1]["trade_date"])
                doc = {"ts_code": ts_code, "trade_date": trade_date, **signals}
                ops.append(UpdateOne(
                    {"ts_code": ts_code, "trade_date": trade_date},
                    {"$set": doc},
                    upsert=True,
                ))

                if len(ops) >= 500:
                    await db["screener_signals"].bulk_write(ops, ordered=False)
                    ops = []

                if (idx + 1) % 100 == 0:
                    print(f"  已处理 {idx + 1}/{total}")
            except Exception as e:
                print(f"  {ts_code} 信号计算失败: {e}")

        if ops:
            await db["screener_signals"].bulk_write(ops, ordered=False)
    finally:
        client.close()
    print("✅ 筛选信号计算完成")


if __name__ == "__main__":
    asyncio.run(run())
