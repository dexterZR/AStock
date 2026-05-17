from fastapi import APIRouter, Depends, Query
from app.models.response import BaseResponse
from app.services.stock_service import StockService
from app.repos.stock_repo import StockRepo
from app.api.deps import get_db
from motor.motor_asyncio import AsyncIOMotorDatabase
import time

router = APIRouter(prefix="/api/stocks", tags=["股票"])

_overview_cache: dict = {"data": None, "ts": 0, "ttl": 120}


async def get_stock_service(db: AsyncIOMotorDatabase = Depends(get_db)) -> StockService:
    return StockService(StockRepo(db))


@router.get("")
async def list_stocks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    service: StockService = Depends(get_stock_service),
):
    data = await service.get_stock_list(skip, limit)
    return BaseResponse(data=data)


@router.get("/overview")
async def market_overview(db: AsyncIOMotorDatabase = Depends(get_db)):
    global _overview_cache
    now = time.time()
    if _overview_cache["data"] is not None and now - _overview_cache["ts"] < _overview_cache["ttl"]:
        return BaseResponse(data=_overview_cache["data"])

    latest = await db["daily_quotes"].find_one(
        {"adjust_flag": "none"},
        {"trade_date": 1},
        sort=[("trade_date", -1)],
    )
    if not latest:
        return BaseResponse(data={
            "total_stocks": 0, "up_count": 0, "down_count": 0, "flat_count": 0,
            "limit_up_count": 0, "limit_down_count": 0, "turnover_total": 0,
        })

    trade_date = latest["trade_date"]
    docs = await db["daily_quotes"].find(
        {"adjust_flag": "none", "trade_date": trade_date},
        {"pct_change": 1, "close": 1, "amount": 1},
    ).to_list(None)

    up = sum(1 for d in docs if d.get("pct_change", 0) > 0)
    down = sum(1 for d in docs if d.get("pct_change", 0) < 0)
    flat = sum(1 for d in docs if d.get("pct_change", 0) == 0)
    limit_up = sum(1 for d in docs if d.get("pct_change", 0) >= 9.9)
    limit_down = sum(1 for d in docs if d.get("pct_change", 0) <= -9.9)
    data = {
        "total_stocks": len(docs), "up_count": up, "down_count": down, "flat_count": flat,
        "limit_up_count": limit_up, "limit_down_count": limit_down, "turnover_total": round(sum(d.get("amount", 0) for d in docs) / 1e8, 2),
    }
    _overview_cache["data"] = data
    _overview_cache["ts"] = now
    return BaseResponse(data=data)


@router.get("/top/up")
async def top_up(limit: int = Query(10, ge=1, le=50), db: AsyncIOMotorDatabase = Depends(get_db)):
    pipeline = [
        {"$match": {"adjust_flag": "none"}},
        {"$sort": {"trade_date": -1}},
        {"$group": {"_id": "$ts_code", "quote": {"$first": "$$ROOT"}}},
        {"$sort": {"quote.pct_change": -1}},
        {"$limit": limit},
    ]
    docs = await db["daily_quotes"].aggregate(pipeline).to_list(limit)
    result = []
    for d in docs:
        q = d["quote"]
        result.append({"ts_code": d["_id"], "name": "", "pct_change": q.get("pct_change", 0)})
    # Fill names from stocks
    codes = [r["ts_code"] for r in result]
    names = await db["stocks"].find({"ts_code": {"$in": codes}}, {"name": 1, "ts_code": 1}).to_list(None)
    name_map = {n["ts_code"]: n.get("name", "") for n in names}
    for r in result:
        r["name"] = name_map.get(r["ts_code"], r["ts_code"])
    return BaseResponse(data=result)


@router.get("/top/down")
async def top_down(limit: int = Query(10, ge=1, le=50), db: AsyncIOMotorDatabase = Depends(get_db)):
    pipeline = [
        {"$match": {"adjust_flag": "none"}},
        {"$sort": {"trade_date": -1}},
        {"$group": {"_id": "$ts_code", "quote": {"$first": "$$ROOT"}}},
        {"$sort": {"quote.pct_change": 1}},
        {"$limit": limit},
    ]
    docs = await db["daily_quotes"].aggregate(pipeline).to_list(limit)
    result = []
    for d in docs:
        q = d["quote"]
        result.append({"ts_code": d["_id"], "name": "", "pct_change": q.get("pct_change", 0)})
    codes = [r["ts_code"] for r in result]
    names = await db["stocks"].find({"ts_code": {"$in": codes}}, {"name": 1, "ts_code": 1}).to_list(None)
    name_map = {n["ts_code"]: n.get("name", "") for n in names}
    for r in result:
        r["name"] = name_map.get(r["ts_code"], r["ts_code"])
    return BaseResponse(data=result)


@router.get("/search/{keyword}")
async def search_stocks(
    keyword: str,
    limit: int = Query(20, ge=1, le=50),
    service: StockService = Depends(get_stock_service),
):
    data = await service.search_stocks(keyword, limit)
    return BaseResponse(data=data)


# ===== 市场概览 & 涨跌榜 =====
@router.get("/{ts_code}")
async def get_stock(ts_code: str, service: StockService = Depends(get_stock_service)):
    data = await service.get_stock_detail(ts_code)
    return BaseResponse(data=data)


