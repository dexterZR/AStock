"""
测试 ScreenerRepo — MongoDB 聚合筛选
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.repos.screener_repo import ScreenerRepo
from app.models.screener import ScreenerCondition


def _make_mongo_cursor(return_value):
    cursor = MagicMock()
    cursor.sort = MagicMock(return_value=cursor)
    cursor.limit = MagicMock(return_value=cursor)
    cursor.to_list = AsyncMock(return_value=return_value)
    return cursor


@pytest.fixture
def mock_db():
    db = MagicMock()
    db["screener_snapshot"] = MagicMock()
    db["stocks"] = MagicMock()
    return db


@pytest.fixture
def repo(mock_db):
    return ScreenerRepo(mock_db)


# ============================================================
class TestScreenViaSnapshot:
    @pytest.fixture
    def repo_with_snapshot(self, mock_db):
        mock_db["screener_snapshot"].find_one = AsyncMock(return_value={
            "snapshot_date": "20250115"
        })
        return ScreenerRepo(mock_db)

    async def test_basic_snapshot_query(self, repo_with_snapshot, mock_db):
        mock_results = [
            {"ts_code": "000001.SZ", "name": "平安银行", "close": 12.5, "pct_change": 2.3},
        ]
        mock_db["screener_snapshot"].aggregate = MagicMock(return_value=_make_mongo_cursor(mock_results))
        conditions = [
            ScreenerCondition(category="technical", field="ma_bullish", op="eq", value=True),
        ]
        results = await repo_with_snapshot.screen_with_conditions(conditions, limit=10)
        assert len(results) == 1
        assert results[0]["ts_code"] == "000001.SZ"

    async def test_industry_filter_snapshot(self, repo_with_snapshot, mock_db):
        mock_db["screener_snapshot"].aggregate = MagicMock(return_value=_make_mongo_cursor([]))
        conditions = [
            ScreenerCondition(category="quote", field="industry", op="in_", values=["银行", "白酒"]),
        ]
        results = await repo_with_snapshot.screen_with_conditions(conditions, limit=10)
        assert isinstance(results, list)

    async def test_pe_range_snapshot(self, repo_with_snapshot, mock_db):
        mock_db["screener_snapshot"].aggregate = MagicMock(return_value=_make_mongo_cursor([]))
        conditions = [
            ScreenerCondition(category="fundamental", field="pe", op="range", min=0, max=20),
        ]
        results = await repo_with_snapshot.screen_with_conditions(conditions, limit=10)
        assert isinstance(results, list)

    async def test_multiple_conditions_snapshot(self, repo_with_snapshot, mock_db):
        mock_db["screener_snapshot"].aggregate = MagicMock(return_value=_make_mongo_cursor([]))
        conditions = [
            ScreenerCondition(category="technical", field="ma_bullish", op="eq", value=True),
            ScreenerCondition(category="technical", field="volume_surge", op="eq", value=True),
            ScreenerCondition(category="fundamental", field="pe", op="range", min=0, max=30),
        ]
        results = await repo_with_snapshot.screen_with_conditions(conditions, limit=20)
        assert isinstance(results, list)


class TestScreenViaPipeline:
    async def test_pipeline_fallback(self, repo, mock_db):
        mock_db["screener_snapshot"].find_one = AsyncMock(return_value=None)
        mock_db["stocks"].aggregate = MagicMock(return_value=_make_mongo_cursor([]))
        conditions = [
            ScreenerCondition(category="fundamental", field="roe", op="gt", value=15),
        ]
        results = await repo.screen_with_conditions(conditions, limit=10)
        assert isinstance(results, list)

    async def test_pipeline_with_industry_and_technical(self, repo, mock_db):
        mock_db["screener_snapshot"].find_one = AsyncMock(return_value=None)

        # stocks.aggregate 返回 cursor
        mock_db["stocks"].aggregate = MagicMock(return_value=_make_mongo_cursor([]))

        # stocks.find (行业预筛) 返回 cursor
        codes_cursor = MagicMock()
        codes_cursor.limit = MagicMock(return_value=codes_cursor)
        codes_cursor.to_list = AsyncMock(return_value=[{"ts_code": "000001.SZ"}])
        mock_db["stocks"].find = MagicMock(return_value=codes_cursor)

        conditions = [
            ScreenerCondition(category="technical", field="rsi_oversold", op="eq", value=True),
            ScreenerCondition(category="quote", field="industry", op="in_", values=["半导体"]),
        ]
        results = await repo.screen_with_conditions(conditions)
        assert isinstance(results, list)

    async def test_pipeline_returns_project_fields(self, repo, mock_db):
        mock_db["screener_snapshot"].find_one = AsyncMock(return_value=None)
        mock_results = [{
            "ts_code": "600519.SH", "name": "贵州茅台", "industry": "白酒",
            "market": "主板", "close": 1800.0, "pct_change": 1.5,
            "turnover_rate": 0.5, "volume": 100000, "amount": 1.8e10,
            "pe": 35.0, "pb": 8.0, "roe": 25.0, "total_mv": 2.2e12,
            "signals": {"ma_bullish": True},
        }]
        mock_db["stocks"].aggregate = MagicMock(return_value=_make_mongo_cursor(mock_results))
        results = await repo.screen_with_conditions([], limit=10)
        assert len(results) == 1
        result = results[0]
        for key in ["ts_code", "name", "close", "pct_change", "pe", "roe"]:
            assert key in result, f"缺少字段 {key}"


class TestGetIndustries:
    async def test_get_industries(self, mock_db):
        mock_db["stocks"].distinct = MagicMock(return_value=["银行", "白酒", "电力"])
        repo = ScreenerRepo(mock_db)
        result = await repo.get_industries()
        assert isinstance(result, list)
        assert len(result) >= 1


class TestApplyCondition:
    def test_range_condition(self, repo):
        match = {}
        c = ScreenerCondition(category="fundamental", field="pe", op="range", min=0, max=20)
        repo._apply_condition(match, "pe", c)
        assert match["pe"] == {"$gte": 0, "$lte": 20}

    def test_gt_condition(self, repo):
        match = {}
        c = ScreenerCondition(category="fundamental", field="roe", op="gt", value=15)
        repo._apply_condition(match, "roe", c)
        assert match["roe"] == {"$gt": 15}

    def test_lt_condition(self, repo):
        match = {}
        c = ScreenerCondition(category="fundamental", field="pe", op="lt", value=30)
        repo._apply_condition(match, "pe", c)
        assert match["pe"] == {"$lt": 30}

    def test_eq_condition(self, repo):
        match = {}
        c = ScreenerCondition(category="technical", field="ma_bullish", op="eq", value=True)
        repo._apply_condition(match, "ma_bullish", c)
        assert match["ma_bullish"] is True
