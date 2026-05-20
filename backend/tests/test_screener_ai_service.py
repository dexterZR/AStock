"""
测试 ScreenerAIService — AI选股对话、关键词解析、流式对话
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.screener_ai_service import (
    ScreenerAIService, FAST_KEYWORD_MAP,
    _build_system_prompt, _build_chat_system_prompt,
    _build_chat_stream_system_prompt, _parse_llm_result,
)
from app.models.screener import ScreenerCondition


# ============================================================
def _make_mongo_cursor(return_value):
    cursor = MagicMock()
    cursor.sort = MagicMock(return_value=cursor)
    cursor.limit = MagicMock(return_value=cursor)
    cursor.to_list = AsyncMock(return_value=return_value)
    return cursor


@pytest.fixture
def mock_db():
    db = MagicMock()
    # stocks collection
    db["stocks"] = MagicMock()
    db["stocks"].distinct = MagicMock(return_value=["银行", "白酒", "电力", "半导体", "医药", "航空"])
    # screener collections
    db["screener_snapshot"] = MagicMock()
    db["screener_snapshot"].find_one = AsyncMock(return_value=None)
    db["screener_snapshot"].aggregate = MagicMock(return_value=_make_mongo_cursor([]))
    # llm_config — 默认不配置
    db["llm_config"] = MagicMock()
    db["llm_config"].find_one = AsyncMock(return_value=None)
    # daily recommendations
    db["ai_daily_recommendations"] = MagicMock()
    db["ai_daily_recommendations"].find_one = AsyncMock(return_value=None)
    db["ai_daily_recommendations"].replace_one = AsyncMock(return_value=MagicMock())
    return db


@pytest.fixture
def ai_service(mock_db):
    return ScreenerAIService(mock_db)


# ============================================================
class TestKeywordMatch:
    def test_golden_cross_keyword(self):
        assert "金叉" in FAST_KEYWORD_MAP
        assert FAST_KEYWORD_MAP["金叉"][0].field == "macd_cross"

    def test_oversold_keywords(self):
        for kw in ["超卖", "超跌", "超跌反弹", "底部", "抄底", "见底"]:
            assert kw in FAST_KEYWORD_MAP, f"缺少关键词: {kw}"
            assert FAST_KEYWORD_MAP[kw][0].field == "rsi_oversold"

    def test_volume_keywords(self):
        assert "放量" in FAST_KEYWORD_MAP
        assert FAST_KEYWORD_MAP["放量"][0].field == "volume_surge"
        assert "缩量" in FAST_KEYWORD_MAP
        assert FAST_KEYWORD_MAP["缩量"][0].field == "volume_shrink"

    def test_fundamental_keywords(self):
        assert "低估值" in FAST_KEYWORD_MAP
        assert FAST_KEYWORD_MAP["低估值"][0].field == "pe"
        assert "高ROE" in FAST_KEYWORD_MAP
        assert "高股息" in FAST_KEYWORD_MAP

    def test_breakout_keywords(self):
        assert "突破" in FAST_KEYWORD_MAP
        assert FAST_KEYWORD_MAP["突破"][0].field == "breakout_20d_high"

    def test_all_conditions_are_valid(self):
        valid = {"technical", "fundamental", "pattern", "quote"}
        for kw, conds in FAST_KEYWORD_MAP.items():
            for c in conds:
                assert c.category in valid, f"{kw}: {c.category}"


class TestParseNaturalLanguage:
    @patch("app.services.screener_ai_service._get_llm_config")
    async def test_keyword_only_no_llm(self, mock_llm_config, ai_service):
        """无 LLM 配置时，纯关键词匹配"""
        mock_llm_config.return_value = {"api_key": "", "base_url": "", "model": "", "name": ""}
        result = await ai_service.parse_natural_language("寻找近期MACD金叉的股票")
        assert result["source"] == "keyword"
        assert len(result["matched_keywords"]) >= 1
        assert any("金叉" in kw for kw in result["matched_keywords"])
        assert len(result["conditions"]) >= 1

    @patch("app.services.screener_ai_service._get_llm_config")
    async def test_multiple_keywords(self, mock_llm_config, ai_service):
        mock_llm_config.return_value = {"api_key": "", "base_url": "", "model": "", "name": ""}
        result = await ai_service.parse_natural_language("放量突破的低估值龙头")
        assert result["source"] == "keyword"
        assert len(result["matched_keywords"]) >= 2
        cond_fields = {c["field"] for c in result["conditions"]}
        assert len(cond_fields) >= 2

    @patch("app.services.screener_ai_service._get_llm_config")
    async def test_empty_query_fallback(self, mock_llm_config, ai_service):
        result = await ai_service.parse_natural_language("abcdefghijk")
        assert result["source"] == "keyword"
        assert len(result["conditions"]) >= 1


class TestAIPick:
    @patch("app.services.screener_ai_service._get_llm_config")
    async def test_ai_pick_with_keywords(self, mock_llm_config, ai_service):
        mock_llm_config.return_value = {"api_key": "", "base_url": "", "model": "", "name": ""}
        result = await ai_service.ai_pick("金叉放量")
        assert result["source"] == "keyword"
        assert "stocks" in result

    @patch("app.services.screener_ai_service._get_llm_config")
    async def test_ai_pick_no_match_fallback(self, mock_llm_config, ai_service):
        mock_llm_config.return_value = {"api_key": "", "base_url": "", "model": "", "name": ""}
        result = await ai_service.ai_pick("xyzzy12345")
        assert "stocks" in result


class TestAIChat:
    @patch("app.services.screener_ai_service._get_llm_config")
    async def test_ai_chat_no_llm_fallback(self, mock_llm_config, ai_service):
        mock_llm_config.return_value = {"api_key": "", "base_url": "", "model": "", "name": ""}
        result = await ai_service.ai_chat("找金叉股票", [])
        assert "text" in result
        assert "conditions" in result
        assert "stocks" in result

    @patch("app.services.screener_ai_service._get_llm_config")
    async def test_ai_chat_with_history(self, mock_llm_config, ai_service):
        mock_llm_config.return_value = {"api_key": "", "base_url": "", "model": "", "name": ""}
        history = [
            {"role": "user", "content": "帮我找低估值股票"},
            {"role": "assistant", "content": "好的，帮你筛选PE<25的股票"},
        ]
        result = await ai_service.ai_chat("再加上高ROE", history)
        assert "text" in result


class TestAIAnalyze:
    @patch("app.services.screener_ai_service._get_llm_config")
    async def test_ai_analyze_multiple_codes(self, mock_llm_config, ai_service, mock_db):
        mock_llm_config.return_value = {"api_key": "", "base_url": "", "model": "", "name": ""}
        quotes = [{"ts_code": "000001.SZ", "trade_date": "20250101", "close": 10.0,
                    "volume": 10000, "amount": 1e7, "pct_change": 1.0, "adjust_flag": "none"}]
        db_quotes = MagicMock()
        db_quotes.find = MagicMock(return_value=_make_mongo_cursor(quotes))
        mock_db["daily_quotes"] = db_quotes
        db_inds = MagicMock()
        db_inds.find = MagicMock(return_value=_make_mongo_cursor([]))
        mock_db["indicators"] = db_inds

        result = await ai_service.ai_analyze(["000001.SZ", "000002.SZ"])
        assert "overview" in result
        assert "stocks" in result
        assert len(result["stocks"]) >= 1


# ============================================================
class TestSystemPrompts:
    def test_build_system_prompt_includes_fields(self):
        prompt = _build_system_prompt(["银行", "白酒", "电力"])
        assert "macd_cross" in prompt
        assert "pe" in prompt
        assert "银行" in prompt
        assert "JSON" in prompt

    def test_build_chat_system_prompt(self):
        prompt = _build_chat_system_prompt(["半导体", "医药"])
        assert "should_search" in prompt
        assert "半导体" in prompt

    def test_build_stream_system_prompt(self):
        prompt = _build_chat_stream_system_prompt(["新能源", "通信"])
        assert "should_search" in prompt
        assert "新能源" in prompt
        assert "json" in prompt.lower()


class TestParseLLMResult:
    def test_valid_result(self):
        llm_result = {
            "conditions": [
                {"category": "technical", "field": "macd_cross", "op": "eq", "value": True},
            ],
            "industries": ["银行", "白酒"],
            "explanation": "筛选MACD金叉、银行白酒行业",
        }
        valid = ["银行", "白酒", "电力", "医药"]
        conds, inds, expl = _parse_llm_result(llm_result, valid)
        assert len(conds) == 1
        assert conds[0].field == "macd_cross"
        assert inds == ["银行", "白酒"]
        assert expl != ""

    def test_invalid_industry_filtered(self):
        llm_result = {
            "conditions": [],
            "industries": ["银行", "不存在的行业"],
            "explanation": "",
        }
        conds, inds, _ = _parse_llm_result(llm_result, ["银行", "白酒"])
        assert inds == ["银行"]

    def test_empty_conditions(self):
        conds, inds, _ = _parse_llm_result(
            {"conditions": [], "industries": [], "explanation": "无"}, ["银行"])
        assert conds == []
        assert inds == []


class TestTagLabel:
    def test_all_common_fields_have_labels(self, ai_service):
        common = ["macd_cross", "volume_surge", "pe", "breakout_20d_high"]
        for field in common:
            label = ai_service._get_tag_label(field)
            assert label, f"字段 {field} 缺少中文标签"


# ============================================================
class TestDailyRecommendation:
    @patch("app.services.screener_ai_service._get_llm_config")
    async def test_generate_daily(self, mock_llm_config, ai_service, mock_db):
        mock_llm_config.return_value = {"api_key": "", "base_url": "", "model": "", "name": ""}
        mock_db["ai_daily_recommendations"].find_one = AsyncMock(return_value=None)
        result = await ai_service._generate_daily_recommendation()
        assert "date" in result
        assert "recommendations" in result
        assert len(result["recommendations"]) >= 2

    @patch("app.services.screener_ai_service._get_llm_config")
    async def test_get_cached_daily(self, mock_llm_config, ai_service, mock_db):
        mock_llm_config.return_value = {"api_key": "", "base_url": "", "model": "", "name": ""}
        cached = {"date": "2025-01-15", "recommendations": []}
        mock_db["ai_daily_recommendations"].find_one = AsyncMock(return_value=cached)
        result = await ai_service.get_daily_recommendation()
        assert result == cached


class TestAIChatStream:
    @patch("app.services.screener_ai_service._get_llm_config")
    async def test_stream_no_llm_fallback(self, mock_llm_config, ai_service):
        mock_llm_config.return_value = {"api_key": "", "base_url": "", "model": "", "name": ""}
        events = []
        async for event in ai_service.ai_chat_stream("找金叉股票", []):
            events.append(event)
        types = [e["type"] for e in events]
        assert "done" in types

    @patch("app.services.screener_ai_service._get_llm_config")
    async def test_stream_llm_configured(self, mock_llm_config, ai_service, mock_db):
        mock_llm_config.return_value = {
            "api_key": "sk-test", "base_url": "https://api.openai.com/v1",
            "model": "gpt-3.5-turbo", "name": "test",
        }
        with patch("openai.AsyncOpenAI") as mock_cls:
            mock_client = MagicMock()
            mock_stream = MagicMock()

            async def _aiter(self):
                items = [
                    MagicMock(choices=[MagicMock(delta=MagicMock(content="你好"))]),
                    MagicMock(choices=[MagicMock(delta=MagicMock(content="，已为你筛选"))]),
                ]
                for item in items:
                    yield item

            mock_stream.__aiter__ = _aiter
            mock_client.chat.completions.create = AsyncMock(return_value=mock_stream)
            mock_cls.return_value = mock_client

            events = []
            async for event in ai_service.ai_chat_stream("找金叉", []):
                events.append(event)
            chunks = [e for e in events if e["type"] == "chunk"]
            assert len(chunks) >= 1
            done_events = [e for e in events if e["type"] == "done"]
            assert len(done_events) >= 1
