import pytest
import json
from unittest.mock import AsyncMock, MagicMock
from app.infrastructure.cache import RedisCache


@pytest.fixture
def mock_redis():
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.setex = AsyncMock(return_value=True)
    redis.delete = AsyncMock(return_value=1)
    redis.set = AsyncMock(return_value=True)
    return redis


@pytest.fixture
def cache(mock_redis):
    return RedisCache(mock_redis)


class TestRedisCache:
    async def test_get_missing_key(self, cache, mock_redis):
        mock_redis.get.return_value = None
        result = await cache.get("nonexistent")
        assert result is None
        mock_redis.get.assert_called_once_with("nonexistent")

    async def test_get_existing_key(self, cache, mock_redis):
        mock_redis.get.return_value = json.dumps({"key": "value"}, ensure_ascii=False)
        result = await cache.get("mykey")
        assert result == {"key": "value"}

    async def test_set_value(self, cache, mock_redis):
        await cache.set("mykey", {"data": 123}, ttl=600)
        mock_redis.setex.assert_called_once()
        args = mock_redis.setex.call_args
        assert args[0][0] == "mykey"
        assert args[0][1] == 600
        assert json.loads(args[0][2]) == {"data": 123}

    async def test_set_default_ttl(self, cache, mock_redis):
        await cache.set("mykey", "val")
        args = mock_redis.setex.call_args
        assert args[0][1] == 300

    async def test_delete_keys(self, cache, mock_redis):
        await cache.delete("key1", "key2")
        mock_redis.delete.assert_called_once_with("key1", "key2")

    async def test_delete_no_keys(self, cache, mock_redis):
        await cache.delete()
        mock_redis.delete.assert_not_called()

    async def test_lock_acquired(self, cache, mock_redis):
        mock_redis.set.return_value = True
        result = await cache.lock("resource", ttl=30)
        assert result is True
        mock_redis.set.assert_called_once_with("lock:resource", "1", nx=True, ex=30)

    async def test_lock_failed(self, cache, mock_redis):
        mock_redis.set.return_value = None
        result = await cache.lock("resource")
        assert result is None

    async def test_unlock(self, cache, mock_redis):
        await cache.unlock("resource")
        mock_redis.delete.assert_called_once_with("lock:resource")

    async def test_set_chinese_value(self, cache, mock_redis):
        await cache.set("name", {"name": "贵州茅台"})
        args = mock_redis.setex.call_args
        stored = json.loads(args[0][2])
        assert stored == {"name": "贵州茅台"}
        assert "贵州茅台" in args[0][2]
