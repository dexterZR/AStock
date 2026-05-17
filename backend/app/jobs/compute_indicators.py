import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.database import get_job_db
from pymongo import UpdateOne


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy().sort_values("trade_date")
    close = df["close"].values
    high = df["high"].values
    low = df["low"].values
    vol = df["volume"].values
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


async def compute_and_save_indicators():
    db, client = await get_job_db()
    try:
        codes = await db["stocks"].distinct("ts_code", {"delist_date": None})
        total = len(codes)
        print(f"开始计算 {total} 只股票的技术指标")
        for idx, ts_code in enumerate(codes):
            try:
                cursor = db["daily_quotes"].find(
                    {"ts_code": ts_code, "adjust_flag": "none"},
                    {"_id": 0, "trade_date": 1, "open": 1, "high": 1, "low": 1,
                     "close": 1, "volume": 1}
                ).sort("trade_date", 1).limit(300)
                rows = await cursor.to_list(length=300)
                if len(rows) < 20:
                    continue
                df = pd.DataFrame(rows)
                df = compute_indicators(df)
                ops = []
                for _, row in df.iterrows():
                    if pd.isna(row.get("trade_date")):
                        continue
                    doc = {
                        "ts_code": ts_code, "trade_date": str(row["trade_date"]),
                        "ma_5": _safe_float(row.get("ma_5")), "ma_10": _safe_float(row.get("ma_10")),
                        "ma_20": _safe_float(row.get("ma_20")), "ma_60": _safe_float(row.get("ma_60")),
                        "macd_dif": _safe_float(row.get("macd_dif")), "macd_dea": _safe_float(row.get("macd_dea")),
                        "macd_bar": _safe_float(row.get("macd_bar")),
                        "rsi_6": _safe_float(row.get("rsi_6")), "rsi_12": _safe_float(row.get("rsi_12")),
                        "rsi_24": _safe_float(row.get("rsi_24")),
                        "kdj_k": _safe_float(row.get("kdj_k")), "kdj_d": _safe_float(row.get("kdj_d")),
                        "kdj_j": _safe_float(row.get("kdj_j")),
                        "boll_upper": _safe_float(row.get("boll_upper")),
                        "boll_mid": _safe_float(row.get("boll_mid")),
                        "boll_lower": _safe_float(row.get("boll_lower")),
                    }
                    ops.append(UpdateOne(
                        {"ts_code": ts_code, "trade_date": str(row["trade_date"])},
                        {"$set": doc}, upsert=True))
                if ops:
                    await db["indicators"].bulk_write(ops, ordered=False)
                if (idx + 1) % 100 == 0:
                    print(f"  已处理 {idx + 1}/{total}")
            except Exception as e:
                print(f"  {ts_code} 计算失败: {e}")
    finally:
        client.close()
    print("✅ 技术指标计算完成")


if __name__ == "__main__":
    import asyncio
    asyncio.run(compute_and_save_indicators())
