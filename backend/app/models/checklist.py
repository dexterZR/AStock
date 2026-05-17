from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class PreTradeChecklist(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    stock_code: str
    stock_name: str
    action: str  # BUY / ADD
    buy_reason: str
    stop_loss_price: float
    target_price: Optional[float] = None
    position_ratio: float  # %
    expected_period: str  # short/medium/long
    risk_level: str  # low/medium/high
    market_env: str  # bull/oscillation/bear
    contrarian_check: bool
    created_at: datetime = Field(default_factory=datetime.now)
