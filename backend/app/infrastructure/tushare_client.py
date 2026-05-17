import asyncio
from abc import ABC, abstractmethod
import akshare as ak
import pandas as pd
from app.core.config import settings

class DataProvider(ABC):
    @abstractmethod
    def get_daily_kline(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame: ...
    @abstractmethod
    def get_stock_list(self) -> pd.DataFrame: ...
    @abstractmethod
    def get_realtime_quotes(self) -> pd.DataFrame: ...

class AkshareProvider(DataProvider):
    def get_daily_kline(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        df = ak.stock_zh_a_hist(
            symbol=symbol,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust="",
        )
        return df

    def get_stock_list(self) -> pd.DataFrame:
        df = ak.stock_info_a_code_name()
        return df

    def get_realtime_quotes(self) -> pd.DataFrame:
        df = ak.stock_zh_a_spot_em()
        return df

class TushareProvider(DataProvider):
    def __init__(self):
        import tushare as ts
        ts.set_token(settings.TUSHARE_TOKEN)
        self.pro = ts.pro_api()

    def get_daily_kline(self, ts_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        return self.pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)

    def get_stock_list(self) -> pd.DataFrame:
        return self.pro.stock_basic(exchange='', list_status='L')

    def get_realtime_quotes(self) -> pd.DataFrame:
        raise NotImplementedError("tushare 不提供实时行情")

class DataClient:
    """统一数据门面，akshare 优先，tushare 备用"""
    def __init__(self):
        self.providers = [AkshareProvider()]
        if settings.TUSHARE_TOKEN:
            self.providers.append(TushareProvider())

    def get_daily_kline(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        for provider in self.providers:
            try:
                return provider.get_daily_kline(symbol, start_date, end_date)
            except Exception as e:
                print(f"[{provider.__class__.__name__}] 失败: {e}")
                continue
        raise RuntimeError("所有数据源均失败")

    def get_stock_list(self) -> pd.DataFrame:
        return self.providers[0].get_stock_list()

    def get_realtime_quotes(self) -> pd.DataFrame:
        return self.providers[0].get_realtime_quotes()

    async def async_get_daily_kline(self, symbol: str, start_date: str, end_date: str):
        return await asyncio.to_thread(self.get_daily_kline, symbol, start_date, end_date)

    async def async_get_realtime_quotes(self):
        return await asyncio.to_thread(self.get_realtime_quotes)

    async def async_get_stock_list(self):
        return await asyncio.to_thread(self.get_stock_list)


data_client = DataClient()
