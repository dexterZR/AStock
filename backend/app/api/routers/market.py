from fastapi import APIRouter, Depends
from app.models.response import BaseResponse
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.api.deps import get_db
import akshare as ak
import asyncio
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/market", tags=["大盘"])

_index_cache = {"data": None, "ts": 0}

async def _fetch_indices():
    now = asyncio.get_event_loop().time()
    if _index_cache["data"] and now - _index_cache["ts"] < 300:
        return _index_cache["data"]

    index_map = {
        "000001.SH": {"symbol": "sh000001", "name": "上证指数"},
        "399001.SZ": {"symbol": "sz399001", "name": "深证成指"},
        "399006.SZ": {"symbol": "sz399006", "name": "创业板指"},
    }
    indices = []
    for code, info in index_map.items():
        try:
            df = await asyncio.to_thread(ak.stock_zh_index_daily, symbol=info["symbol"])
            if df is not None and len(df) >= 2:
                last = df.iloc[-1]
                prev = df.iloc[-2]
                close = float(last["close"])
                prev_close = float(prev["close"])
                pct_change = round((close - prev_close) / prev_close * 100, 2)
                indices.append({"code": code, "name": info["name"], "close": close, "pct_change": pct_change})
            else:
                indices.append({"code": code, "name": info["name"], "close": 0, "pct_change": 0})
        except Exception:
            indices.append({"code": code, "name": info["name"], "close": 0, "pct_change": 0})

    _index_cache["data"] = indices
    _index_cache["ts"] = now
    return indices


@router.get("/overview")
async def market_overview(db: AsyncIOMotorDatabase = Depends(get_db)):
    indices = await _fetch_indices()
    return BaseResponse(data={"indices": indices})
