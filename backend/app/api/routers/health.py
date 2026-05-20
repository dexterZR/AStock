import time
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from redis.asyncio import Redis
from app.api.deps import get_db, get_redis

router = APIRouter(tags=["系统"])


@router.get("/health")
async def health_check():
    return {"status": "ok", "timestamp": int(time.time())}


@router.get("/health/detailed")
async def detailed_health(db: AsyncIOMotorDatabase = Depends(get_db), redis: Redis = Depends(get_redis)):
    checks = {}
    try:
        await db.command("ping")
        checks["mongodb"] = "ok"
    except Exception as e:
        checks["mongodb"] = f"error: {e}"
    try:
        await redis.ping()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {e}"
    all_ok = all(v == "ok" for v in checks.values())
    return {"status": "ok" if all_ok else "degraded", "checks": checks}


@router.get("/health/data-status")
async def data_status(db: AsyncIOMotorDatabase = Depends(get_db)):
    """检查数据新鲜度"""
    latest = await db["daily_quotes"].find_one(
        {"adjust_flag": "none"},
        {"trade_date": 1},
        sort=[("trade_date", -1)],
    )
    stock_count = await db["daily_quotes"].count_documents(
        {"adjust_flag": "none", "trade_date": latest["trade_date"] if latest else ""}
    )
    total_stocks = await db["stocks"].count_documents({})

    today_str = datetime.now().strftime("%Y%m%d")
    last_date = str(latest.get("trade_date", "")) if latest else ""
    is_fresh = last_date == today_str

    return {
        "last_trade_date": last_date,
        "today": today_str,
        "is_fresh": is_fresh,
        "stocks_with_data": stock_count,
        "total_stocks_in_db": total_stocks,
        "message": "✅ 数据已更新" if is_fresh else f"⚠️ 数据日期为 {last_date}，非今日 {today_str}",
    }


@router.post("/sync")
async def trigger_sync(step: str = Query("all", enum=["all", "daily", "fundamentals", "indicators", "signals", "news"])):
    import asyncio
    results = {}

    async def _run(name, coro):
        try:
            await coro
            results[name] = "ok"
        except Exception as e:
            results[name] = f"error: {e}"

    if step in ("all", "daily"):
        from app.jobs.sync_daily import sync_daily_quotes
        await _run("daily_quotes", sync_daily_quotes())

    if step in ("all", "fundamentals"):
        from app.jobs.sync_fundamentals import run as sync_fundamentals
        await _run("fundamentals", sync_fundamentals())

    if step in ("all", "indicators"):
        from app.jobs.compute_indicators import compute_and_save_indicators
        await _run("indicators", compute_and_save_indicators())

    if step in ("all", "signals"):
        from app.jobs.compute_screener_signals import run as compute_signals
        await _run("signals", compute_signals())

    if step == "news":
        from app.jobs.sync_news import sync_all_news
        await _run("news", sync_all_news())

    try:
        from app.api.routers.stocks import _overview_cache
        _overview_cache["data"] = None
    except Exception:
        pass

    try:
        import redis.asyncio as aioredis
        from app.core.config import settings
        r = aioredis.from_url(settings.REDIS_URL)
        await r.flushall()
        await r.close()
    except Exception:
        pass

    return {"status": "ok", "step": step, "results": results}
