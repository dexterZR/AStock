import asyncio
from app.repos.quote_repo import QuoteRepo
from app.infrastructure.cache import RedisCache

INDEX_CODES = {"000001.SH", "399001.SZ", "399006.SZ"}
INDEX_SYMBOL_MAP = {
    "000001.SH": "sh000001",
    "399001.SZ": "sz399001",
    "399006.SZ": "sz399006",
}
INDEX_NAMES = {
    "000001.SH": "上证指数",
    "399001.SZ": "深证成指",
    "399006.SZ": "创业板指",
}


def _is_index(ts_code: str) -> bool:
    return ts_code in INDEX_CODES


# 缓存指数日K线数据（避免每次全量拉取 akshare）
_index_daily_cache: dict[str, list[dict]] = {}
_index_daily_cache_ts: dict[str, float] = {}


async def _fetch_index_daily(ts_code: str, start_date: str, end_date: str):
    import akshare as ak
    symbol = INDEX_SYMBOL_MAP.get(ts_code)
    if not symbol:
        return []

    now_ts = asyncio.get_event_loop().time()
    # 非交易时段缓存 1 小时，交易时段缓存 60 秒
    from datetime import datetime as dt
    is_trading = dt.now().weekday() < 5 and 570 <= dt.now().hour * 60 + dt.now().minute < 900
    cache_ttl = 60 if is_trading else 3600

    if ts_code in _index_daily_cache and (now_ts - _index_daily_cache_ts.get(ts_code, 0)) < cache_ttl:
        cached = _index_daily_cache[ts_code]
        return [r for r in cached if start_date <= r["trade_date"] <= end_date]

    try:
        df = await asyncio.to_thread(ak.stock_zh_index_daily, symbol=symbol)
    except Exception as e:
        import logging
        logging.getLogger("app.quote").error(f"获取指数 {ts_code} K线失败: {e}")
        # 返回缓存中数据
        if ts_code in _index_daily_cache:
            cached = _index_daily_cache[ts_code]
            return [r for r in cached if start_date <= r["trade_date"] <= end_date]
        return []

    if df is None or df.empty:
        return []

    df = df.rename(columns={"date": "trade_date", "volume": "vol"})
    df["trade_date"] = df["trade_date"].astype(str).str.replace("-", "", regex=False)
    result = []
    for _, row in df.iterrows():
        result.append({
            "ts_code": ts_code,
            "trade_date": str(row["trade_date"]),
            "open": float(row["open"]),
            "high": float(row["high"]),
            "low": float(row["low"]),
            "close": float(row["close"]),
            "vol": float(row.get("vol", 0)),
            "volume": float(row.get("vol", 0)),
            "amount": 0,
        })
    if len(result) >= 2:
        for i in range(1, len(result)):
            prev_close = result[i - 1]["close"]
            if prev_close > 0:
                result[i]["pct_change"] = round((result[i]["close"] - prev_close) / prev_close * 100, 2)
    if result:
        result[0]["pct_change"] = result[0].get("pct_change", 0)

    # 缓存完整数据
    _index_daily_cache[ts_code] = result
    _index_daily_cache_ts[ts_code] = asyncio.get_event_loop().time()

    # 返回请求日期范围的数据
    return [r for r in result if start_date <= r["trade_date"] <= end_date]


# 共享缓存：与 market.py 共用新浪实时数据（避免重复调用 sina API）
_sina_spot_cache: list[dict] | None = None
_sina_spot_cache_ts: float = 0


def _try_get_sina_spot_cache(ts_code: str, max_age_sec: int = 30) -> dict | None:
    """从共享的 sina 实时缓存中获取指数行情"""
    global _sina_spot_cache, _sina_spot_cache_ts
    now_ts = asyncio.get_event_loop().time()
    if _sina_spot_cache and (now_ts - _sina_spot_cache_ts) < max_age_sec:
        for item in _sina_spot_cache:
            if item.get("code") == ts_code:
                return {
                    "ts_code": ts_code,
                    "trade_date": item.get("trade_date", ""),
                    "open": item.get("open", 0),
                    "high": item.get("high", 0),
                    "low": item.get("low", 0),
                    "close": item.get("close", 0),
                    "vol": 0,
                    "volume": 0,
                    "amount": 0,
                    "pct_change": item.get("pct_change", 0),
                    "pre_close": item.get("pre_close", 0),
                    "price": item.get("close", 0),
                    "open_price": item.get("open", 0),
                    "high_price": item.get("high", 0),
                    "low_price": item.get("low", 0),
                    "pre_close_price": item.get("pre_close", 0),
                }
    return None


def _set_sina_spot_cache(indices: list[dict]):
    """由 market.py 调用，设置共享的 sina 实时缓存"""
    global _sina_spot_cache, _sina_spot_cache_ts
    _sina_spot_cache = indices
    _sina_spot_cache_ts = asyncio.get_event_loop().time()


async def _fetch_index_latest_from_sina(ts_code: str):
    """从新浪实时接口获取指数最新行情"""
    import akshare as ak
    sina_code_map = {
        "000001.SH": "sh000001",
        "399001.SZ": "sz399001",
        "399006.SZ": "sz399006",
    }
    sina_code = sina_code_map.get(ts_code)
    if not sina_code:
        return None
    try:
        df = await asyncio.to_thread(ak.stock_zh_index_spot_sina)
    except Exception:
        return None
    if df is None or df.empty:
        return None
    for _, row in df.iterrows():
        if str(row.get("代码", "")) == sina_code:
            from datetime import datetime as dt
            close = float(row.get("最新价", 0))
            pre_close = float(row.get("昨收", 0))
            pct_change = float(row.get("涨跌幅", 0))
            return {
                "ts_code": ts_code,
                "trade_date": dt.now().strftime("%Y%m%d"),
                "open": float(row.get("今开", 0)),
                "high": float(row.get("最高", 0)),
                "low": float(row.get("最低", 0)),
                "close": close,
                "vol": float(row.get("成交量", 0)),
                "volume": float(row.get("成交量", 0)),
                "amount": float(row.get("成交额", 0)),
                "pct_change": round(pct_change, 2),
                "pre_close": pre_close,
                "price": close,
                "open_price": float(row.get("今开", 0)),
                "high_price": float(row.get("最高", 0)),
                "low_price": float(row.get("最低", 0)),
                "pre_close_price": pre_close,
            }
    return None


async def _fetch_index_latest(ts_code: str):
    """获取指数最新行情，优先从共享 sina 缓存获取"""
    from datetime import datetime as dt

    # 交易时段 30s 缓存，非交易时段 5min
    is_trading = dt.now().weekday() < 5 and 570 <= dt.now().hour * 60 + dt.now().minute < 900
    max_age = 30 if is_trading else 300

    # 优先从共享 sina 缓存获取（与 market.py 共用）
    cached = _try_get_sina_spot_cache(ts_code, max_age)
    if cached:
        return cached

    # 回退1：日K线缓存
    if ts_code in _index_daily_cache:
        daily = _index_daily_cache[ts_code]
        if daily:
            last = daily[-1]
            if len(daily) >= 2:
                prev = daily[-2]
                pre_close = prev["close"]
                pct_change = round((last["close"] - pre_close) / pre_close * 100, 2) if pre_close > 0 else 0
            else:
                pre_close = last["close"]
                pct_change = 0
            return {
                "ts_code": ts_code,
                "trade_date": last["trade_date"],
                "open": last["open"],
                "high": last["high"],
                "low": last["low"],
                "close": last["close"],
                "vol": last.get("vol", 0),
                "volume": last.get("volume", 0),
                "amount": 0,
                "pct_change": pct_change,
                "pre_close": pre_close,
                "price": last["close"],
                "open_price": last["open"],
                "high_price": last["high"],
                "low_price": last["low"],
                "pre_close_price": pre_close,
            }

    # 回退2：直接调用 akshare sina spot API
    result = await _fetch_index_latest_from_sina(ts_code)
    if result:
        return result

    # 回退3：akshare 日K
    import akshare as ak
    symbol = INDEX_SYMBOL_MAP.get(ts_code)
    if not symbol:
        return None
    try:
        df = await asyncio.to_thread(ak.stock_zh_index_daily, symbol=symbol)
    except Exception as e:
        import logging
        logging.getLogger("app.quote").error(f"获取指数 {ts_code} 最新价失败: {e}")
        return None

    if df is None or df.empty or len(df) < 2:
        return None
    last = df.iloc[-1]
    prev = df.iloc[-2]
    close = float(last["close"])
    prev_close = float(prev["close"])
    pct_change = round((close - prev_close) / prev_close * 100, 2) if prev_close > 0 else 0
    return {
        "ts_code": ts_code,
        "trade_date": str(last["date"]).replace("-", "")[:8],
        "open": float(last["open"]),
        "high": float(last["high"]),
        "low": float(last["low"]),
        "close": close,
        "vol": float(last.get("volume", 0)),
        "volume": float(last.get("volume", 0)),
        "amount": 0,
        "pct_change": pct_change,
        "pre_close": prev_close,
        "price": close,
        "open_price": float(last["open"]),
        "high_price": float(last["high"]),
        "low_price": float(last["low"]),
        "pre_close_price": prev_close,
    }


class QuoteService:
    def __init__(self, repo: QuoteRepo, cache: RedisCache):
        self.repo = repo
        self.cache = cache

    async def get_daily_quotes(self, ts_code: str, start_date: str, end_date: str):
        if _is_index(ts_code):
            return await _fetch_index_daily(ts_code, start_date, end_date)

        cache_key = f"daily:{ts_code}:{start_date}:{end_date}"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        data = await self.repo.find_daily(ts_code, start_date, end_date)
        if data:
            await self.cache.set(cache_key, data, ttl=300)
        return data

    async def get_latest_quote(self, ts_code: str):
        if _is_index(ts_code):
            return await _fetch_index_latest(ts_code)

        cache_key = f"latest:{ts_code}"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        data = await self.repo.find_latest(ts_code)
        if data:
            prev = await self.repo.find_previous(ts_code, data.get("trade_date"))
            if prev:
                data["pre_close"] = prev.get("close")

            data["price"] = data.get("close")
            data["open_price"] = data.get("open")
            data["high_price"] = data.get("high")
            data["low_price"] = data.get("low")
            data["pre_close_price"] = data.get("pre_close")

            await self.cache.set(cache_key, data, ttl=300)
        return data
