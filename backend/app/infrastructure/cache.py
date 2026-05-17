import json
import hashlib
from typing import Optional, Any
from redis.asyncio import Redis


class RedisCache:
    def __init__(self, redis: Redis):
        self.redis = redis

    async def get(self, key: str) -> Optional[Any]:
        raw = await self.redis.get(key)
        if raw is None:
            return None
        return json.loads(raw)

    async def set(self, key: str, value: Any, ttl: int = 300):
        await self.redis.setex(key, ttl, json.dumps(value, ensure_ascii=False))

    async def delete(self, *keys: str):
        if keys:
            await self.redis.delete(*keys)

    async def lock(self, key: str, ttl: int = 10) -> bool:
        return await self.redis.set(f"lock:{key}", "1", nx=True, ex=ttl)

    async def unlock(self, key: str):
        await self.redis.delete(f"lock:{key}")
