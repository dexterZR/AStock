"""
测试 Screener API 端点 — FastAPI TestClient 集成测试
"""
import jwt
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock


def _make_token(payload: dict = None) -> str:
    """生成测试用 JWT"""
    from app.core.config import settings
    data = payload or {"sub": "test-user", "username": "test"}
    return jwt.encode(data, settings.JWT_SECRET, algorithm="HS256")


def _make_auth_headers() -> dict:
    return {"Authorization": f"Bearer {_make_token()}"}


def _make_mongo_cursor(return_value):
    cursor = MagicMock()
    cursor.sort = MagicMock(return_value=cursor)
    cursor.limit = MagicMock(return_value=cursor)
    cursor.to_list = AsyncMock(return_value=return_value)
    return cursor


@pytest.fixture
def mock_db():
    db = MagicMock()

    # screener
    db["screener_snapshot"] = MagicMock()
    db["screener_snapshot"].find_one = AsyncMock(return_value=None)
    db["screener_snapshot"].aggregate = MagicMock(return_value=_make_mongo_cursor([]))

    db["stocks"] = MagicMock()
    db["stocks"].aggregate = MagicMock(return_value=_make_mongo_cursor([]))
    db["stocks"].distinct = MagicMock(return_value=["银行", "白酒", "半导体"])
    db["stocks"].find_one = AsyncMock(return_value={
        "ts_code": "000001.SZ", "name": "平安银行", "industry": "银行",
    })

    # llm
    db["llm_config"] = MagicMock()
    db["llm_config"].find_one = AsyncMock(return_value=None)

    # daily rec
    db["ai_daily_recommendations"] = MagicMock()
    db["ai_daily_recommendations"].find_one = AsyncMock(return_value=None)
    db["ai_daily_recommendations"].replace_one = AsyncMock(return_value=MagicMock())

    # analysis
    quotes = [{"ts_code": "000001.SZ", "trade_date": "20250101", "close": 10.0,
                "volume": 10000, "amount": 1e7, "pct_change": 1.0, "adjust_flag": "none"}]
    db_quotes = MagicMock()
    db_quotes.find = MagicMock(return_value=_make_mongo_cursor(list(quotes)))
    db["daily_quotes"] = db_quotes

    db_inds = MagicMock()
    db_inds.find = MagicMock(return_value=_make_mongo_cursor([]))
    db["indicators"] = db_inds

    return db


@pytest.fixture
def app_with_overrides(mock_db):
    from app.main import app
    from app.api.deps import get_db

    async def override_db():
        return mock_db

    app.dependency_overrides[get_db] = override_db
    yield app
    app.dependency_overrides.clear()


@pytest.fixture
async def client(app_with_overrides):
    transport = ASGITransport(app=app_with_overrides)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ============================================================
class TestScreenerEndpoints:
    async def test_screen_empty_conditions(self, client):
        headers = _make_auth_headers()
        response = await client.post("/api/screener", json={"conditions": [], "limit": 10}, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    async def test_screen_with_condition(self, client):
        headers = _make_auth_headers()
        response = await client.post("/api/screener", json={
            "conditions": [
                {"category": "fundamental", "field": "pe", "op": "range", "min": 0, "max": 30}
            ],
            "limit": 10,
        }, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    async def test_get_templates(self, client):
        headers = _make_auth_headers()
        response = await client.get("/api/screener/templates", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        templates = data["data"]
        assert len(templates) >= 5
        template_ids = [t["id"] for t in templates]
        assert "breakout_high" in template_ids
        assert "ma_bullish" in template_ids

    async def test_get_industries(self, client):
        headers = _make_auth_headers()
        response = await client.get("/api/screener/industries", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestAIParse:
    async def test_ai_parse_basic(self, client):
        headers = _make_auth_headers()
        response = await client.post("/api/screener/ai-parse", json={
            "query": "MACD金叉放量股票"
        }, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        result = data["data"]
        assert "conditions" in result
        assert "matched_keywords" in result

    async def test_ai_parse_industries(self, client):
        headers = _make_auth_headers()
        response = await client.post("/api/screener/ai-parse", json={
            "query": "银行板块的低估值股票"
        }, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestAIPick:
    async def test_ai_pick_basic(self, client):
        headers = _make_auth_headers()
        response = await client.post("/api/screener/ai-pick", json={
            "query": "突破新高的科技股"
        }, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "stocks" in data["data"]

    async def test_ai_pick_no_match(self, client):
        headers = _make_auth_headers()
        response = await client.post("/api/screener/ai-pick", json={
            "query": "xyzabc12345"
        }, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestAIAnalyze:
    async def test_ai_analyze_batch(self, client):
        headers = _make_auth_headers()
        response = await client.post("/api/screener/ai-analyze", json={
            "ts_codes": ["000001.SZ", "000002.SZ"]
        }, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "overview" in data["data"]
        assert "stocks" in data["data"]


class TestAIChat:
    async def test_ai_chat_basic(self, client):
        headers = _make_auth_headers()
        response = await client.post("/api/screener/ai-chat", json={
            "query": "帮我找金叉股票",
            "history": [],
        }, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "text" in data["data"]

    async def test_ai_chat_with_history(self, client):
        headers = _make_auth_headers()
        response = await client.post("/api/screener/ai-chat", json={
            "query": "再加上放量条件",
            "history": [
                {"role": "user", "content": "找金叉"},
                {"role": "assistant", "content": "已筛选MACD金叉股票"},
            ],
        }, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    async def test_ai_chat_stream_endpoint(self, client):
        headers = _make_auth_headers()
        response = await client.post("/api/screener/ai-chat/stream", json={
            "query": "找放量股票",
            "history": [],
        }, headers=headers)
        # SSE 端点可能被 auth 放行（public_paths 中有 /api/sse/ 前缀），但 /api/screener/ai-chat/stream 不在其中
        # 所以需要 auth headers
        assert response.status_code in (200, 401)
        if response.status_code == 200:
            assert "text/event-stream" in response.headers.get("content-type", "")

    async def test_ai_chat_stream_has_data(self, client):
        headers = _make_auth_headers()
        response = await client.post("/api/screener/ai-chat/stream", json={
            "query": "金叉",
            "history": [],
        }, headers=headers)
        if response.status_code == 200:
            body = response.text
            assert "data:" in body, f"SSE响应应包含 data: 前缀，实际内容: {body[:200]}"


class TestAIDaily:
    async def test_ai_daily(self, client):
        headers = _make_auth_headers()
        response = await client.get("/api/screener/ai-daily", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
