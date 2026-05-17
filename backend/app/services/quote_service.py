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


async def _fetch_index_daily(ts_code: str, start_date: str, end_date: str):
    import akshare as ak
    symbol = INDEX_SYMBOL_MAP.get(ts_code)
    if not symbol:
        return []
    df = await asyncio.to_thread(ak.stock_zh_index_daily, symbol=symbol)
    if df is None or df.empty:
        return []
    df = df.rename(columns={"date": "trade_date", "volume": "vol"})
    df["trade_date"] = df["trade_date"].astype(str).str.replace("-", "", regex=False)
    df = df[(df["trade_date"] >= start_date) & (df["trade_date"] <= end_date)]
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
    return result


async def _fetch_index_latest(ts_code: str):
    import akshare as ak
    symbol = INDEX_SYMBOL_MAP.get(ts_code)
    if not symbol:
        return None
    df = await asyncio.to_thread(ak.stock_zh_index_daily, symbol=symbol)
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
