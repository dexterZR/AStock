import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.api.errors import AppError, NotFoundError, ValidationError, ExternalAPIError


# ============================================================
# 共享测试工具：模拟 MongoDB cursor / collection
# ============================================================

class FakeCursor:
    """模拟 Motor cursor — 支持链式调用 sort/limit + async to_list"""

    def __init__(self, data: list):
        self._data = list(data)

    def sort(self, field, direction=1):
        if field == "trade_date":
            reverse = direction < 0
            self._data.sort(key=lambda x: x.get("trade_date", ""), reverse=reverse)
        return self

    def limit(self, n):
        self._data = self._data[:n]
        return self

    async def to_list(self, length=None):
        result = list(self._data)
        if length is not None:
            result = result[:length]
        return result


class FakeCollection:
    """模拟 Motor collection"""

    def __init__(self, cursor_data=None):
        self._cursor_data = cursor_data or []

    def find(self, *args, **kwargs):
        return FakeCursor(self._cursor_data)


class FakeDB(dict):
    """模拟 AsyncIOMotorDatabase — dict 子类"""
    pass


# ============================================================
# 全局 fixtures
# ============================================================


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.command = AsyncMock(return_value={"ok": 1})
    db["stocks"] = MagicMock()
    db["daily_quotes"] = MagicMock()
    return db


@pytest.fixture
def mock_redis():
    redis = AsyncMock()
    redis.ping = AsyncMock(return_value=True)
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock(return_value=True)
    redis.setex = AsyncMock(return_value=True)
    redis.delete = AsyncMock(return_value=1)
    redis.incr = AsyncMock(return_value=1)
    redis.expire = AsyncMock(return_value=True)
    redis.pipeline = MagicMock()
    redis.pipeline.return_value.execute = AsyncMock(return_value=[1, True])
    redis.pipeline.return_value.incr = MagicMock(return_value=redis.pipeline.return_value)
    redis.pipeline.return_value.expire = MagicMock(return_value=redis.pipeline.return_value)
    return redis


@pytest.fixture
def app_with_overrides(mock_db, mock_redis):
    from app.main import app
    from app.api.deps import get_db, get_redis

    async def override_get_db():
        return mock_db

    async def override_get_redis():
        return mock_redis

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis
    yield app
    app.dependency_overrides.clear()
