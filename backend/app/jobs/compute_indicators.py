import pandas as pd
import numpy as np
import asyncio
from datetime import datetime, timedelta
from app.core.database import get_job_db
from pymongo import UpdateOne


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy().sort_values("trade_date")
    for p in [5, 10, 20, 60, 120, 250]:
        df[f"ma_{p}"] = df["close"].rolling(window=p).mean()
    ema12 = df["close"].ewm(span=12, adjust=False).mean()
    ema26 = df["close"].ewm(span=26, adjust=False).mean()
    df["macd_dif"] = ema12 - ema26
    df["macd_dea"] = df["macd_dif"].ewm(span=9, adjust=False).mean()
    df["macd_bar"] = 2 * (df["macd_dif"] - df["macd_dea"])
    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)
    for p in [6, 12, 24]:
        avg_gain = gain.ewm(alpha=1/p, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/p, adjust=False).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        df[f"rsi_{p}"] = 100 - (100 / (1 + rs))
    low_n = df["low"].rolling(window=9).min()
    high_n = df["high"].rolling(window=9).max()
    denom = (high_n - low_n).replace(0, np.nan)
    rsv = (df["close"] - low_n) / denom * 100
    rsv = rsv.fillna(50.0)
    df["kdj_k"] = rsv.ewm(com=2, adjust=False).mean()
    df["kdj_d"] = df["kdj_k"].ewm(com=2, adjust=False).mean()
    df["kdj_j"] = 3 * df["kdj_k"] - 2 * df["kdj_d"]
    df["boll_mid"] = df["close"].rolling(window=20).mean()
    std20 = df["close"].rolling(window=20).std()
    df["boll_upper"] = df["boll_mid"] + 2 * std20
    df["boll_lower"] = df["boll_mid"] - 2 * std20
    return df


def _safe_float(val):
    if val is None or (isinstance(val, float) and (np.isnan(val) or np.isinf(val))):
        return None
    return round(float(val), 4)


_INDICATOR_FIELDS = [
    "ma_5", "ma_10", "ma_20", "ma_60",
    "macd_dif", "macd_dea", "macd_bar",
    "rsi_6", "rsi_12", "rsi_24",
    "kdj_k", "kdj_d", "kdj_j",
    "boll_upper", "boll_mid", "boll_lower",
]


def _row_to_doc(ts_code, row):
    doc = {"ts_code": ts_code, "trade_date": str(row["trade_date"])}
    for f in _INDICATOR_FIELDS:
        doc[f] = _safe_float(row.get(f))
    return doc


async def _process_batch(db, batch_codes):
    pipeline = [
        {"$match": {"ts_code": {"$in": batch_codes}, "adjust_flag": "none"}},
        {"$sort": {"trade_date": 1}},
        {"$group": {
            "_id": "$ts_code",
            "quotes": {"$push": {
                "trade_date": "$trade_date", "open": "$open",
                "high": "$high", "low": "$low", "close": "$close",
                "volume": "$volume",
            }},
        }},
    ]
    groups = await db["daily_quotes"].aggregate(pipeline).to_list(None)

    all_ops = []
    for g in groups:
        ts_code = g["_id"]
        quotes = g["quotes"]
        if len(quotes) < 20:
            continue
        df = pd.DataFrame(quotes)
        df = compute_indicators(df)
        last_row = df.iloc[-1]
        if pd.isna(last_row.get("trade_date")):
            continue
        doc = _row_to_doc(ts_code, last_row)
        all_ops.append(UpdateOne(
            {"ts_code": ts_code, "trade_date": doc["trade_date"]},
            {"$set": doc},
            upsert=True,
        ))

    if all_ops:
        await db["indicators"].bulk_write(all_ops, ordered=False)
    return len(all_ops)


async def compute_and_save_indicators():
    db, client = await get_job_db()
    try:
        codes = await db["stocks"].distinct("ts_code", {"delist_date": None})
        total = len(codes)
        print(f"开始计算 {total} 只股票的技术指标(增量模式)")

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
    print(f"✅ 技术指标计算完成, 共写入 {total_written} 条")


if __name__ == "__main__":
    asyncio.run(compute_and_save_indicators())
