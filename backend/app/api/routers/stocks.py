from fastapi import APIRouter, Depends, Query
from app.models.response import BaseResponse
from app.services.stock_service import StockService
from app.repos.stock_repo import StockRepo
from app.api.deps import get_db
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter(prefix="/api/stocks", tags=["股票"])


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
    stats = await db["market_stats"].find_one(
        {}, {"_id": 0}, sort=[("trade_date", -1)]
    )
    if stats:
        return BaseResponse(data=stats)

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
    pipeline = [
        {"$match": {"adjust_flag": "none", "trade_date": trade_date}},
        {"$group": {
            "_id": None,
            "total": {"$sum": 1},
            "up": {"$sum": {"$cond": [{"$gt": ["$pct_change", 0]}, 1, 0]}},
            "down": {"$sum": {"$cond": [{"$lt": ["$pct_change", 0]}, 1, 0]}},
            "flat": {"$sum": {"$cond": [{"$eq": ["$pct_change", 0]}, 1, 0]}},
            "limit_up": {"$sum": {"$cond": [{"$gte": ["$pct_change", 9.9]}, 1, 0]}},
            "limit_down": {"$sum": {"$cond": [{"$lte": ["$pct_change", -9.9]}, 1, 0]}},
            "total_amount": {"$sum": "$amount"},
        }},
    ]
    result = await db["daily_quotes"].aggregate(pipeline).to_list(1)
    if result:
        r = result[0]
        data = {
            "trade_date": trade_date,
            "total_stocks": r["total"], "up_count": r["up"], "down_count": r["down"],
            "flat_count": r["flat"], "limit_up_count": r["limit_up"],
            "limit_down_count": r["limit_down"], "turnover_total": round(r["total_amount"] / 1e8, 2),
        }
    else:
        data = {"trade_date": trade_date, "total_stocks": 0, "up_count": 0,
                "down_count": 0, "flat_count": 0, "limit_up_count": 0,
                "limit_down_count": 0, "turnover_total": 0}
    return BaseResponse(data=data)


@router.get("/top/up")
async def top_up(limit: int = Query(10, ge=1, le=50), db: AsyncIOMotorDatabase = Depends(get_db)):
    cached = await db["market_top"].find_one(
        {"type": "up"}, {"_id": 0}, sort=[("trade_date", -1)]
    )
    if cached and cached.get("stocks"):
        return BaseResponse(data=cached["stocks"][:limit])

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
    codes = [r["ts_code"] for r in result]
    names = await db["stocks"].find({"ts_code": {"$in": codes}}, {"name": 1, "ts_code": 1}).to_list(None)
    name_map = {n["ts_code"]: n.get("name", "") for n in names}
    for r in result:
        r["name"] = name_map.get(r["ts_code"], r["ts_code"])
    return BaseResponse(data=result)


@router.get("/top/down")
async def top_down(limit: int = Query(10, ge=1, le=50), db: AsyncIOMotorDatabase = Depends(get_db)):
    cached = await db["market_top"].find_one(
        {"type": "down"}, {"_id": 0}, sort=[("trade_date", -1)]
    )
    if cached and cached.get("stocks"):
        return BaseResponse(data=cached["stocks"][:limit])

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


@router.get("/{ts_code}")
async def get_stock(ts_code: str, service: StockService = Depends(get_stock_service)):
    data = await service.get_stock_detail(ts_code)
    return BaseResponse(data=data)


