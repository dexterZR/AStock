import random
import numpy as np
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient


MOCK_STOCKS = [
    ("平安银行", "000001.SZ", "银行"),
    ("万科A", "000002.SZ", "房地产"),
    ("中兴通讯", "000063.SZ", "通信"),
    ("五粮液", "000858.SZ", "白酒"),
    ("浦发银行", "600000.SH", "银行"),
    ("民生银行", "600016.SH", "银行"),
    ("招商银行", "600036.SH", "银行"),
    ("贵州茅台", "600519.SH", "白酒"),
    ("长江电力", "600900.SH", "电力"),
    ("工商银行", "601398.SH", "银行"),
    ("宁德时代", "300750.SZ", "新能源"),
    ("比亚迪", "002594.SZ", "汽车"),
    ("格力电器", "000651.SZ", "家电"),
    ("中国平安", "601318.SH", "保险"),
    ("中国中免", "601888.SH", "免税"),
    ("海天味业", "603288.SH", "食品"),
    ("美的集团", "000333.SZ", "家电"),
    ("深信泰丰", "002352.SZ", "物流"),
    ("中国中车", "601766.SH", "机械"),
]


def generate_mock_kline(ts_code: str, base_price: float = 10.0, days: int = 365):
    price = base_price
    results = []
    start = datetime(2025, 5, 15)
    
    for i in range(days):
        current = start + timedelta(days=i)
        if current.weekday() >= 5:
            continue
        
        ret = np.random.normal(0.0003, 0.02)
        open_p = round(price, 2)
        close_p = round(price * (1 + ret), 2)
        high_p = round(max(open_p, close_p) + abs(close_p - open_p) * random.random() * 2, 2)
        low_p = round(min(open_p, close_p) - abs(close_p - open_p) * random.random() * 2, 2)
        low_p = max(low_p, 0.01)
        volume = int(np.random.lognormal(15, 1.5))
        amount = round(volume * close_p, 2)
        
        results.append({
            "ts_code": ts_code,
            "trade_date": current.strftime("%Y%m%d"),
            "open": open_p,
            "high": high_p,
            "low": low_p,
            "close": close_p,
            "volume": volume,
            "amount": amount,
            "turnover_rate": round(random.uniform(0.1, 5.0), 2),
            "pct_change": round(ret * 100, 2),
            "pre_close": round(price, 2),
            "is_trading": True,
            "adjust_flag": "none",
        })
        price = close_p
    
    return results


async def seed_mock_data(mongo_uri: str = None):
    if mongo_uri is None:
        from app.core.config import settings
        mongo_uri = settings.MONGO_URI
    client = AsyncIOMotorClient(mongo_uri)
    db = client["stock_analysis"]
    
    # 清空旧数据
    await db["stocks"].delete_many({})
    await db["daily_quotes"].delete_many({})
    
    # 灌入股票基础信息
    stocks = []
    for name, code, industry in MOCK_STOCKS:
        stocks.append({
            "ts_code": code,
            "symbol": code.split(".")[0],
            "name": name,
            "industry": industry,
            "market": "主板" if code.startswith(("600", "000")) else "创业板",
            "list_date": "20100101",
            "delist_date": None,
            "is_st": False,
        })
    await db["stocks"].insert_many(stocks)
    print(f"灌入 {len(stocks)} 只股票基础信息")
    
    # 灌入日K线
    base_prices = [15.0, 8.5, 25.0, 140.0, 10.0, 7.8, 35.0, 1680.0,
                   20.0, 5.5, 180.0, 250.0, 35.0, 80.0, 120.0, 90.0,
                   55.0, 25.0, 75.0, 8.0]
    
    for (name, code, _), base_price in zip(MOCK_STOCKS, base_prices):
        klines = generate_mock_kline(code, base_price=base_price, days=365)
        if klines:
            await db["daily_quotes"].insert_many(klines)
    
    print("灌入日K线数据完成")
    client.close()
    print("✅ Mock 数据灌入完成")


if __name__ == "__main__":
    import asyncio
    asyncio.run(seed_mock_data())
