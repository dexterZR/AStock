from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from redis.asyncio import Redis
from app.core.config import settings

mongo_client: AsyncIOMotorClient = None
redis_client: Redis = None
db: AsyncIOMotorDatabase = None


async def connect_db():
    global mongo_client, redis_client, db
    mongo_client = AsyncIOMotorClient(
        settings.MONGO_URI,
        maxPoolSize=settings.MONGO_MAX_POOL,
        serverSelectionTimeoutMS=5000,
    )
    db = mongo_client[settings.MONGO_DB]
    redis_client = Redis.from_url(
        settings.REDIS_URL,
        max_connections=settings.REDIS_MAX_CONNECTIONS,
        decode_responses=True,
    )
    # 验证连接
    await db.command("ping")
    await redis_client.ping()
    print("✅ MongoDB + Redis 连接成功")


async def close_db():
    if mongo_client:
        mongo_client.close()
    if redis_client:
        await redis_client.close()
    print("✅ 数据库连接已关闭")


def get_db() -> AsyncIOMotorDatabase:
    if db is None:
        raise RuntimeError("Database not initialized. Call connect_db() first.")
    return db


async def get_job_db():
    """供独立 Job 脚本使用的数据库连接，返回 (db, client) 元组"""
    from app.core.config import settings
    client = AsyncIOMotorClient(
        settings.MONGO_URI,
        maxPoolSize=settings.MONGO_MAX_POOL,
        serverSelectionTimeoutMS=5000,
    )
    db = client[settings.MONGO_DB]
    return db, client
