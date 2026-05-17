from fastapi import APIRouter, Depends
from typing import Optional, List
from app.models.response import BaseResponse
from app.services.portfolio_service import PortfolioService
from app.services.event_service import EventService
from app.api.deps import get_db
from app.models.trade import TradeCreate, DecisionCreate, DecisionReview, CostLineUpdate, SharesUpdate
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter(prefix="/api/portfolio", tags=["持仓"])


async def get_portfolio_service(db: AsyncIOMotorDatabase = Depends(get_db)) -> PortfolioService:
    return PortfolioService(db)


async def get_event_service(db: AsyncIOMotorDatabase = Depends(get_db)) -> EventService:
    return EventService(db)


@router.get("/holdings")
async def get_holdings(service: PortfolioService = Depends(get_portfolio_service)):
    data = await service.get_holdings()
    return BaseResponse(data=data)


@router.post("/trades")
async def add_trade(trade: TradeCreate, service: PortfolioService = Depends(get_portfolio_service)):
    trade_id = await service.add_trade(trade.model_dump())
    return BaseResponse(data={"trade_id": trade_id})


@router.get("/trades")
async def get_trades(ts_code: Optional[str] = None, service: PortfolioService = Depends(get_portfolio_service)):
    data = await service.get_trades(ts_code)
    return BaseResponse(data=data)


@router.post("/decisions")
async def add_decision_log(log: DecisionCreate, service: PortfolioService = Depends(get_portfolio_service)):
    log_id = await service.add_decision_log(log.model_dump())
    return BaseResponse(data={"log_id": log_id})


@router.get("/decisions")
async def get_decision_logs(ts_code: Optional[str] = None, service: PortfolioService = Depends(get_portfolio_service)):
    data = await service.get_decision_logs(ts_code)
    return BaseResponse(data=data)


@router.post("/decisions/{log_id}/review")
async def review_decision(log_id: str, result: DecisionReview, service: PortfolioService = Depends(get_portfolio_service)):
    await service.review_decision(log_id, result.model_dump())
    return BaseResponse(data={"reviewed": True})


@router.get("/stats")
async def get_stats(service: PortfolioService = Depends(get_portfolio_service)):
    data = await service.get_trade_stats()
    return BaseResponse(data=data)


# 事件相关API
@router.post("/events")
async def add_event(event: dict, service: EventService = Depends(get_event_service)):
    event_id = await service.add_event(event)
    return BaseResponse(data={"event_id": event_id})


@router.get("/events")
async def get_events(ts_code: Optional[str] = None, days: int = 30, service: EventService = Depends(get_event_service)):
    data = await service.get_events(ts_code, days)
    return BaseResponse(data=data)


@router.get("/alerts")
async def get_alerts(acknowledged: Optional[bool] = None, service: EventService = Depends(get_event_service)):
    data = await service.get_risk_alerts(acknowledged)
    return BaseResponse(data=data)


@router.post("/alerts/{alert_id}/ack")
async def ack_alert(alert_id: str, service: EventService = Depends(get_event_service)):
    await service.acknowledge_alert(alert_id)
    return BaseResponse(data={"acknowledged": True})


@router.get("/daily-brief")
async def daily_brief(service: EventService = Depends(get_event_service)):
    holdings = await PortfolioService(service.db).get_holdings()
    ts_codes = [h["ts_code"] for h in holdings]
    data = await service.generate_daily_brief(ts_codes)
    return BaseResponse(data=data)


# ===== 成本线 =====
@router.get("/cost-lines/{ts_code}")
async def get_cost_lines(ts_code: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    doc = await db["cost_lines"].find_one({"ts_code": ts_code}, {"_id": 0})
    if not doc:
        # 从 trades 推断成本
        trades = await db["trades"].find({"ts_code": ts_code, "action": "buy"}).to_list(None)
        if trades:
            total_cost = sum(t["price"] * t["shares"] for t in trades)
            total_shares = sum(t["shares"] for t in trades)
            avg = round(total_cost / total_shares, 3) if total_shares > 0 else 0
            doc = {
                "ts_code": ts_code, "cost_price": avg,
                "add_price": None, "reduce_price": None, "stop_loss_price": None,
                "position_qty": total_shares,
            }
        else:
            return BaseResponse(data=None)
    return BaseResponse(data=doc)


@router.put("/cost-lines/{ts_code}")
async def update_cost_lines(ts_code: str, body: CostLineUpdate, db: AsyncIOMotorDatabase = Depends(get_db)):
    if body.stop_loss_price and body.cost_price:
        if body.stop_loss_price >= body.cost_price:
            from fastapi import HTTPException
            raise HTTPException(400, "止损价应低于成本价")
    await db["cost_lines"].update_one(
        {"ts_code": ts_code},
        {"$set": {**body.model_dump(), "ts_code": ts_code}},
        upsert=True,
    )
    return BaseResponse(data={"updated": True})


# ===== 股数编辑 =====
@router.put("/shares/{ts_code}")
async def update_shares(ts_code: str, body: SharesUpdate, db: AsyncIOMotorDatabase = Depends(get_db)):
    """更新持仓股数（调整买入记录）"""
    new_shares = body.shares
    if new_shares <= 0:
        from fastapi import HTTPException
        raise HTTPException(400, "股数必须大于0")
    trade = await db["trades"].find_one(
        {"ts_code": ts_code, "action": "buy"}, sort=[("trade_date", -1)]
    )
    if not trade:
        raise HTTPException(404, "未找到买入记录")
    price = trade["price"]
    await db["trades"].update_one(
        {"_id": trade["_id"]},
        {"$set": {"shares": new_shares, "total_amount": price * new_shares}}
    )
    return BaseResponse(data={"updated": True, "shares": new_shares})
