import json
from typing import Optional, Any
from redis.asyncio import Redis

CACHE_PREFIX = "cache:"


class RedisCache:
    def __init__(self, redis: Redis):
        self.redis = redis

    def _prefixed(self, key: str) -> str:
        return f"{CACHE_PREFIX}{key}" if not key.startswith(CACHE_PREFIX) else key

    async def get(self, key: str) -> Optional[Any]:
        raw = await self.redis.get(self._prefixed(key))
        if raw is None:
            return None
        return json.loads(raw)

    async def set(self, key: str, value: Any, ttl: int = 300):
        await self.redis.setex(self._prefixed(key), ttl, json.dumps(value, ensure_ascii=False))

    async def delete(self, *keys: str):
        if keys:
            await self.redis.delete(*(self._prefixed(k) for k in keys))

    async def exists(self, key: str) -> bool:
        return await self.redis.exists(self._prefixed(key)) > 0

    async def get_or_set(self, key: str, factory, ttl: int = 300) -> Any:
        cached = await self.get(key)
        if cached is not None:
            return cached
        value = await factory()
        await self.set(key, value, ttl)
        return value

    async def lock(self, key: str, ttl: int = 10) -> bool:
        return await self.redis.set(f"lock:{key}", "1", nx=True, ex=ttl)

    async def unlock(self, key: str):
        await self.redis.delete(f"lock:{key}")
