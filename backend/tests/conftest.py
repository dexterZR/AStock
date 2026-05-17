import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.api.errors import AppError, NotFoundError, ValidationError, ExternalAPIError


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
