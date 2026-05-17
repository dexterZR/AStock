from pydantic import BaseModel
from typing import Optional

class RealtimeQuote(BaseModel):
    ts_code: str
    close: float
    pct_change: float
    volume: int
    amount: float
    bid: Optional[float] = None
    ask: Optional[float] = None
