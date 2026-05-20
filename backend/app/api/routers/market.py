from fastapi import APIRouter, Depends
from app.models.response import BaseResponse
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.api.deps import get_db
import akshare as ak
import asyncio
import logging
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/market", tags=["大盘"])
logger = logging.getLogger("app.market")

_index_cache = {"data": None, "ts": 0}
_fetch_lock = asyncio.Lock()

INDEX_MAP = {
    "000001.SH": {"symbol": "sh000001", "name": "上证指数", "sina_code": "sh000001"},
    "399001.SZ": {"symbol": "sz399001", "name": "深证成指", "sina_code": "sz399001"},
    "399006.SZ": {"symbol": "sz399006", "name": "创业板指", "sina_code": "sz399006"},
}

# 盘中缓存缩短至 30 秒，确保数据及时更新
CACHE_TTL_INTRADAY = 30   # 交易时段
CACHE_TTL_OFFHOURS = 300  # 非交易时段


def _is_trading_time() -> bool:
    """判断当前是否在 A 股交易时段（周一至周五 9:30-15:00）"""
    now = datetime.now()
    if now.weekday() >= 5:
        return False
    t = now.hour * 60 + now.minute
    return 570 <= t < 900  # 09:30 - 15:00


async def _fetch_indices_from_sina() -> list[dict]:
    """从新浪实时接口获取三大指数行情（数据最新）"""
    try:
        df = await asyncio.to_thread(ak.stock_zh_index_spot_sina)
    except Exception as e:
        logger.warning(f"sina 指数接口异常: {e}")
        return []

    if df is None or df.empty:
        return []

    indices = []
    sina_codes = {info["sina_code"]: (code, info["name"]) for code, info in INDEX_MAP.items()}
    for _, row in df.iterrows():
        sina_code = str(row.get("代码", ""))
        if sina_code not in sina_codes:
            continue
        code, name = sina_codes[sina_code]
        close = float(row.get("最新价", 0))
        pct_change = float(row.get("涨跌幅", 0))
        pre_close = float(row.get("昨收", 0))
        trade_date = datetime.now().strftime("%Y%m%d")
        indices.append({
            "code": code,
            "name": name,
            "close": close,
            "pct_change": round(pct_change, 2),
            "trade_date": trade_date,
            "open": float(row.get("今开", 0)),
            "high": float(row.get("最高", 0)),
            "low": float(row.get("最低", 0)),
            "pre_close": pre_close,
        })

    # 设置共享缓存供 quote_service 使用
    try:
        from app.services.quote_service import _set_sina_spot_cache
        _set_sina_spot_cache(indices)
    except Exception:
        pass

    return indices


async def _fetch_indices_from_daily() -> list[dict]:
    """从 akshare 日K线接口获取三大指数（备用数据源）"""
    indices = []
    for code, info in INDEX_MAP.items():
        try:
            df = await asyncio.to_thread(ak.stock_zh_index_daily, symbol=info["symbol"])
            if df is not None and len(df) >= 2:
                last = df.iloc[-1]
                prev = df.iloc[-2]
                close = float(last["close"])
                prev_close = float(prev["close"])
                pct_change = round((close - prev_close) / prev_close * 100, 2)
                indices.append({
                    "code": code,
                    "name": info["name"],
                    "close": close,
                    "pct_change": pct_change,
                    "trade_date": str(last["date"]).replace("-", "")[:8],
                    "open": float(last.get("open", 0)),
                    "high": float(last.get("high", 0)),
                    "low": float(last.get("low", 0)),
                    "pre_close": prev_close,
                })
            else:
                logger.warning(f"akshare daily 返回 {info['name']} 数据不足")
                if _index_cache["data"]:
                    cached = next((x for x in _index_cache["data"] if x["code"] == code), None)
                    if cached:
                        indices.append(cached)
                        continue
                indices.append({"code": code, "name": info["name"], "close": 0, "pct_change": 0})
        except Exception as e:
            logger.error(f"获取 {info['name']} 指数日K失败: {e}")
            if _index_cache["data"]:
                cached = next((x for x in _index_cache["data"] if x["code"] == code), None)
                if cached:
                    indices.append(cached)
                    continue
            indices.append({"code": code, "name": info["name"], "close": 0, "pct_change": 0})
    return indices


async def _fetch_indices(force: bool = False):
    """
    获取三大指数最新数据。
    优先使用新浪实时接口，失败时回退到日K线接口。
    使用 async lock 防止并发重复请求 akshare。
    """
    now_ts = asyncio.get_event_loop().time()
    cache_ttl = CACHE_TTL_INTRADAY if _is_trading_time() else CACHE_TTL_OFFHOURS

    if not force and _index_cache["data"] and (now_ts - _index_cache["ts"]) < cache_ttl:
        return _index_cache["data"]

    async with _fetch_lock:
        # 双重检查：可能其他协程已刷新缓存
        if not force and _index_cache["data"] and (now_ts - _index_cache["ts"]) < cache_ttl:
            return _index_cache["data"]

        # 优先使用新浪实时接口（数据最新最全）
        indices = await _fetch_indices_from_sina()
        if indices and len(indices) >= 3:
            logger.debug("使用新浪实时接口获取指数数据")
        else:
            # 回退到日K线接口
            logger.info("新浪接口数据不完整，回退到日K线接口")
            indices = await _fetch_indices_from_daily()

        _index_cache["data"] = indices
        _index_cache["ts"] = asyncio.get_event_loop().time()
        return indices


@router.get("/overview")
async def market_overview(db: AsyncIOMotorDatabase = Depends(get_db)):
    indices = await _fetch_indices()
    return BaseResponse(data={"indices": indices})
