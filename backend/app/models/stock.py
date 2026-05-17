from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class StockBase(BaseModel):
    ts_code: str
    symbol: str
    name: str
    industry: Optional[str] = None
    market: Optional[str] = None
    list_date: Optional[str] = None


class StockCreate(StockBase):
    pass


class StockResponse(StockBase):
    class Config:
        from_attributes = True


class DailyQuote(BaseModel):
    ts_code: str
    trade_date: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    amount: float
    turnover_rate: Optional[float] = None
    pct_change: Optional[float] = None
    pre_close: Optional[float] = None
    is_trading: bool = True
    adjust_flag: Optional[str] = "none"


class Indicator(BaseModel):
    ts_code: str
    trade_date: str
    ma_5: Optional[float] = None
    ma_10: Optional[float] = None
    ma_20: Optional[float] = None
    ma_60: Optional[float] = None
    macd_dif: Optional[float] = None
    macd_dea: Optional[float] = None
    macd_bar: Optional[float] = None
    rsi_6: Optional[float] = None
    rsi_12: Optional[float] = None
    rsi_24: Optional[float] = None
    kdj_k: Optional[float] = None
    kdj_d: Optional[float] = None
    kdj_j: Optional[float] = None
    boll_upper: Optional[float] = None
    boll_mid: Optional[float] = None
    boll_lower: Optional[float] = None
