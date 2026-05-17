from typing import List, Dict, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.screener import ScreenerCondition, StrategyTemplate
from app.repos.screener_repo import ScreenerRepo

STRATEGY_TEMPLATES = [
    StrategyTemplate(
        id="breakout_high",
        name="突破新高",
        icon="🚀",
        description="突破20日新高，放量确认，均线多头支撑",
        conditions=[
            ScreenerCondition(category="pattern", field="breakout_20d_high", op="eq", value=True),
            ScreenerCondition(category="technical", field="volume_surge", op="eq", value=True),
            ScreenerCondition(category="technical", field="ma_bullish", op="eq", value=True),
        ]
    ),
    StrategyTemplate(
        id="ma_bullish",
        name="均线多头",
        icon="📈",
        description="MA5>MA10>MA20>MA60，MACD金叉确认",
        conditions=[
            ScreenerCondition(category="technical", field="ma_bullish", op="eq", value=True),
            ScreenerCondition(category="technical", field="macd_cross", op="eq", value=True),
        ]
    ),
    StrategyTemplate(
        id="oversold_bounce",
        name="超跌反弹",
        icon="🔄",
        description="RSI超卖区，股价跌破布林下轨，缩量见底",
        conditions=[
            ScreenerCondition(category="technical", field="rsi_oversold", op="eq", value=True),
            ScreenerCondition(category="technical", field="boll_breakout_down", op="eq", value=True),
            ScreenerCondition(category="technical", field="volume_shrink", op="eq", value=True),
        ]
    ),
    StrategyTemplate(
        id="low_valuation",
        name="低估值",
        icon="💰",
        description="PE低于20，ROE高于15%，股息率超过3%",
        conditions=[
            ScreenerCondition(category="fundamental", field="pe", op="range", min=0, max=20),
            ScreenerCondition(category="fundamental", field="roe", op="gt", value=15),
            ScreenerCondition(category="fundamental", field="dividend_yield", op="gt", value=3),
        ]
    ),
    StrategyTemplate(
        id="volume_attack",
        name="放量上攻",
        icon="🔥",
        description="换手率超5%，涨幅超3%，主力资金净买入",
        conditions=[
            ScreenerCondition(category="quote", field="turnover_rate", op="gt", value=5),
            ScreenerCondition(category="quote", field="pct_change", op="gt", value=3),
            ScreenerCondition(category="capital", field="main_net_buy", op="gt", value=0),
        ]
    ),
    StrategyTemplate(
        id="north_buy",
        name="北向加仓",
        icon="🏦",
        description="北向资金增持，PE低于30，均线多头排列",
        conditions=[
            ScreenerCondition(category="capital", field="north_holding_change", op="gt", value=0),
            ScreenerCondition(category="fundamental", field="pe", op="range", min=0, max=30),
            ScreenerCondition(category="technical", field="ma_bullish", op="eq", value=True),
        ]
    ),
]

class ScreenerService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.repo = ScreenerRepo(db)
        self.db = db

    async def screen(self, conditions: List[ScreenerCondition], limit: int = 50) -> List[dict]:
        return await self.repo.screen_with_conditions(conditions, limit)

    async def get_templates(self) -> List[dict]:
        return [t.model_dump() for t in STRATEGY_TEMPLATES]

    async def get_template_by_id(self, template_id: str) -> Optional[StrategyTemplate]:
        for t in STRATEGY_TEMPLATES:
            if t.id == template_id:
                return t
        return None

    async def get_industries(self) -> List[str]:
        return await self.repo.get_industries()
