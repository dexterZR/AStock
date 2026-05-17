from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class TradeRecord(BaseModel):
    """单笔交易记录"""
    id: Optional[str] = None
    ts_code: str
    name: str
    action: str  # "buy" / "sell"
    price: float
    shares: int
    total_amount: float
    trade_date: str  # YYYYMMDD
    cost_basis: Optional[float] = None
    decision_logic: str
    emotion: str  # "calm" / "greedy" / "fearful" / "impulsive"
    market_view: str
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    tags: List[str] = []
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class HoldingPosition(BaseModel):
    """当前持仓"""
    ts_code: str
    name: str
    total_shares: int
    avg_cost: float
    total_cost: float
    latest_price: Optional[float] = None
    market_value: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    unrealized_pnl_pct: Optional[float] = None
    first_buy_date: Optional[str] = None
    last_trade_date: Optional[str] = None
    risk_level: str = "normal"
    warning_events: List[str] = []


class DecisionLog(BaseModel):
    """决策日志"""
    id: Optional[str] = None
    trade_id: str
    ts_code: str
    action: str
    pre_decision_score: int
    post_result_pnl: Optional[float] = None
    post_result_pct: Optional[float] = None
    attribution: Optional[str] = None
    lessons: Optional[str] = None
    reviewed_at: Optional[str] = None


class StockEvent(BaseModel):
    """个股事件"""
    id: Optional[str] = None
    ts_code: str
    name: str
    event_type: str
    event_date: str
    title: str
    content: str
    source: str
    severity: str = "info"
    is_resolved: bool = False
    resolved_date: Optional[str] = None
    impact_assessment: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class RiskAlert(BaseModel):
    """风险预警"""
    id: Optional[str] = None
    ts_code: str
    name: str
    alert_type: str
    alert_level: str
    title: str
    description: str
    triggered_at: str
    is_acknowledged: bool = False
    acknowledged_at: Optional[str] = None
    related_event_id: Optional[str] = None
