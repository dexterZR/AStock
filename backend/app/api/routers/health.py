import time
from fastapi import APIRouter, Depends
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
