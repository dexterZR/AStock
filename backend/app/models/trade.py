from pydantic import BaseModel, Field
from typing import Optional, List

class TradeCreate(BaseModel):
    ts_code: str = Field(..., description="股票代码，如 600519.SH")
    name: str = Field(..., description="股票名称")
    action: str = Field(..., pattern="^(buy|sell)$", description="buy 或 sell")
    price: float = Field(..., gt=0, description="成交价格")
    shares: int = Field(..., gt=0, description="成交数量")
    trade_date: str = Field(..., description="交易日期 YYYYMMDD")
    decision_logic: str = Field("", description="决策逻辑")
    emotion: str = Field("calm", description="交易情绪")
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    market_view: Optional[str] = Field(None, description="大盘看法/市场观点")
    tags: List[str] = Field(default_factory=list)

class DecisionCreate(BaseModel):
    stock_code: str
    stock_name: str
    action: str
    content: str
    tags: List[str] = Field(default_factory=list)

class DecisionReview(BaseModel):
    pnl: Optional[float] = None
    pnl_pct: Optional[float] = None
    attribution: Optional[str] = None
    lessons: Optional[str] = None

class CostLineUpdate(BaseModel):
    cost_price: Optional[float] = Field(None, gt=0)
    stop_loss_price: Optional[float] = Field(None, gt=0)
    add_price: Optional[float] = Field(None, gt=0)
    reduce_price: Optional[float] = Field(None, gt=0)

class SharesUpdate(BaseModel):
    shares: int = Field(..., gt=0)
