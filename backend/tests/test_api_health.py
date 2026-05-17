import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.api.deps import get_db, get_redis
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.command = AsyncMock(return_value={"ok": 1})
    return db


@pytest.fixture
def mock_redis():
    redis = AsyncMock()
    redis.ping = AsyncMock(return_value=True)
    return redis


@pytest.fixture
async def client(mock_db, mock_redis):
    async def override_get_db():
        return mock_db

    async def override_get_redis():
        return mock_redis

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


class TestHealthEndpoint:
    async def test_health_check(self, client):
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "timestamp" in data

    async def test_root(self, client):
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["version"] == "1.0.0"
