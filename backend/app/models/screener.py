from pydantic import BaseModel
from typing import Optional, List, Literal, Any


class ScreenerCondition(BaseModel):
    category: Literal["technical", "fundamental", "pattern", "quote"]
    field: str
    op: Literal["eq", "gt", "gte", "lt", "lte", "range", "in_"]
    value: Optional[Any] = None
    min: Optional[float] = None
    max: Optional[float] = None
    values: Optional[List] = None


class ScreenerRequest(BaseModel):
    conditions: List[ScreenerCondition] = []
    limit: int = 50


class AIParseRequest(BaseModel):
    query: str


class AIPickRequest(BaseModel):
    query: str


class AIAnalyzeRequest(BaseModel):
    ts_codes: List[str]


class AIChatRequest(BaseModel):
    query: str
    history: List[dict] = []


class AIChatResponse(BaseModel):
    text: str
    conditions: List[dict] = []
    industries: List[str] = []
    stocks: List[dict] = []
    stock_count: int = 0


class StrategyTemplate(BaseModel):
    id: str
    name: str
    icon: str
    description: str
    conditions: List[ScreenerCondition]


class ScreenerSignal(BaseModel):
    ts_code: str
    trade_date: str
    ma5_cross_ma10: Optional[bool] = None
    ma5_cross_ma20: Optional[bool] = None
    ma10_cross_ma20: Optional[bool] = None
    macd_cross: Optional[bool] = None
    kdj_cross: Optional[bool] = None
    rsi_oversold: Optional[bool] = None
    rsi_overbought: Optional[bool] = None
    boll_breakout_up: Optional[bool] = None
    boll_breakout_down: Optional[bool] = None
    ma_bullish: Optional[bool] = None
    ma_bearish: Optional[bool] = None
    volume_surge: Optional[bool] = None
    volume_shrink: Optional[bool] = None
    breakout_20d_high: Optional[bool] = None
    breakout_60d_high: Optional[bool] = None
    drop_20d_low: Optional[bool] = None
    v_shape_recovery: Optional[bool] = None
    consolidation: Optional[bool] = None
    continuous_up_3d: Optional[bool] = None
    continuous_volume_3d: Optional[bool] = None


class FundamentalData(BaseModel):
    ts_code: str
    trade_date: str
    pe: Optional[float] = None
    pb: Optional[float] = None
    roe: Optional[float] = None
    revenue_growth: Optional[float] = None
    profit_growth: Optional[float] = None
    dividend_yield: Optional[float] = None
    total_mv: Optional[float] = None
    circ_mv: Optional[float] = None

