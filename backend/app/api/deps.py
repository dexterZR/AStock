from motor.motor_asyncio import AsyncIOMotorDatabase
from redis.asyncio import Redis
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from app.core.config import settings

security = HTTPBearer(auto_error=False)


async def get_db() -> AsyncIOMotorDatabase:
    from app.core.database import db
    return db


async def get_redis() -> Redis:
    from app.core.database import redis_client
    return redis_client


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials is None:
        raise HTTPException(401, "未登录")
    try:
        payload = jwt.decode(credentials.credentials, settings.JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token 已过期")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Token 无效")
