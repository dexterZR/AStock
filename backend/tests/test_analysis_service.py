"""
测试 MultiAgentAnalysisService — 三维度分析 + LLM 深度报告
"""
import pytest
import asyncio as aio
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.analysis_service import MultiAgentAnalysisService, INDUSTRY_WEIGHTS
from tests.helpers import FakeDB, FakeCollection


def _make_quotes(n: int = 30, base_price: float = 50.0, step: float = 0.5) -> list[dict]:
    """生成模拟K线 — 日期升序（旧→新）"""
    quotes = []
    for i in range(n):
        quotes.append({
            "ts_code": "600519.SH",
            "trade_date": f"202501{i+1:02d}",
            "open": base_price + i * step,
            "high": base_price + i * step + 0.5,
            "low": base_price + i * step - 0.3,
            "close": base_price + i * step,
            "volume": 100000 + i * 1000,
            "amount": 5e8 + i * 1e6,
            "pct_change": 0.2,
            "adjust_flag": "none",
        })
    return quotes


def _make_indicators(n: int = 30, macd_last_few: float = 0.3) -> list[dict]:
    """生成模拟技术指标"""
    indicators = []
    for i in range(n):
        signs = {
            "ts_code": "600519.SH",
            "trade_date": f"202501{i+1:02d}",
            "macd_bar": macd_last_few if i >= n - 3 else -0.1,
            "rsi_6": 55.0,
            "rsi_12": 52.0,
            "rsi_24": 50.0,
            "kdj_k": 60.0,
            "kdj_d": 55.0,
        }
        indicators.append(signs)
    return indicators


def _make_stock(**overrides) -> dict:
    stock = {
        "ts_code": "600519.SH",
        "name": "贵州茅台",
        "industry": "白酒",
        "total_cap": 2e12,
    }
    stock.update(overrides)
    return stock


def _setup_db(db, quotes, indicators, stock, llm_config=None):
    db["daily_quotes"] = FakeCollection(quotes)
    db["indicators"] = FakeCollection(indicators)
    db["stocks"] = FakeCollection()
    db["stocks"].find_one = AsyncMock(return_value=stock)
    db["llm_config"] = FakeCollection()
    db["llm_config"].find_one = AsyncMock(return_value=llm_config)


# ============================================================
@pytest.fixture
def mock_db():
    db = FakeDB()
    _setup_db(db, _make_quotes(), _make_indicators(), _make_stock())
    return db


@pytest.fixture
def service(mock_db):
    return MultiAgentAnalysisService(mock_db)


# ============================================================
class TestAnalyzeStock:
    async def test_returns_all_dimensions(self, service):
        result = await service.analyze_stock("600519.SH")
        assert result["ts_code"] == "600519.SH"
        assert result["name"] == "贵州茅台"
        assert isinstance(result["total_score"], (int, float))
        assert "technical" in result
        assert result["technical"]["dimension"] == "技术面"
        assert "fundamental" in result
        assert "catalyst" in result
        assert "bull_bear_analysis" in result
        assert "key_signals" in result
        assert "operation_suggestion" in result
        assert "verdict" in result
        assert "llm_deep_report" in result
        assert result["llm_deep_report"]["source"] == "fallback"

    async def test_batch_filters_and_sorts(self, service):
        codes = [f"00000{i}.SZ" for i in range(1, 30)]
        results = await service.analyze_batch(codes)
        scores = [r.get("total_score", 0) for r in results]
        assert scores == sorted(scores, reverse=True)


class TestInsufficientData:
    async def test_insufficient_data_placeholder(self, mock_db):
        _setup_db(mock_db, _make_quotes(5), _make_indicators(30), _make_stock())
        service = MultiAgentAnalysisService(mock_db)
        result = await service.analyze_stock("000001.SZ")
        assert result["total_score"] == 0
        assert result["data_insufficient"] is True
        assert "数据不足" in result["verdict"]["action"]


class TestTechnicalAgent:
    async def test_ma_bullish(self, mock_db):
        """强上升趋势 → 技术面高分"""
        quotes = _make_quotes(30, base_price=30.0, step=5.0)  # 30→175
        _setup_db(mock_db, quotes, _make_indicators(), _make_stock())
        service = MultiAgentAnalysisService(mock_db)
        result = await service.analyze_stock("600519.SH")
        tech = result["technical"]
        assert tech["score"] > 50, f"多头趋势分数={tech['score']}"

    async def test_rsi_overbought(self, mock_db):
        indicators = _make_indicators(30)
        indicators[-1]["rsi_6"] = 85.0
        _setup_db(mock_db, _make_quotes(), indicators, _make_stock())
        service = MultiAgentAnalysisService(mock_db)
        result = await service.analyze_stock("600519.SH")
        tech = result["technical"]
        assert any("超买" in r for r in tech.get("reasons", []))

    async def test_macd_golden_cross(self, mock_db):
        indicators = _make_indicators(30)
        indicators[-2]["macd_bar"] = -0.1
        indicators[-1]["macd_bar"] = 0.3
        _setup_db(mock_db, _make_quotes(), indicators, _make_stock())
        service = MultiAgentAnalysisService(mock_db)
        result = await service.analyze_stock("600519.SH")
        tech = result["technical"]
        assert any("金叉" in r for r in tech.get("reasons", []))

    async def test_volume_surge(self, mock_db):
        quotes = _make_quotes(30)
        avg_vol = sum(q["volume"] for q in quotes[:-1]) / 29
        quotes[-1]["volume"] = avg_vol * 4  # 4倍放量
        quotes[-1]["close"] = quotes[-2]["close"] + 5
        _setup_db(mock_db, quotes, _make_indicators(), _make_stock())
        service = MultiAgentAnalysisService(mock_db)
        result = await service.analyze_stock("600519.SH")
        tech = result["technical"]
        assert any("放量" in r for r in tech.get("reasons", []))


class TestFundamentalAgent:
    async def test_industry_bonus(self, mock_db):
        _setup_db(mock_db, _make_quotes(), _make_indicators(), _make_stock(industry="白酒"))
        service = MultiAgentAnalysisService(mock_db)
        result = await service.analyze_stock("600519.SH")
        fund = result["fundamental"]
        assert any("白酒" in r for r in fund.get("reasons", []))

    async def test_large_cap(self, mock_db):
        _setup_db(mock_db, _make_quotes(), _make_indicators(), _make_stock(total_cap=5e12))
        service = MultiAgentAnalysisService(mock_db)
        result = await service.analyze_stock("600519.SH")
        fund = result["fundamental"]
        assert "大盘" in fund.get("cap_analysis", "")

    async def test_low_liquidity(self, mock_db):
        quotes = _make_quotes(30)
        for q in quotes:
            q["amount"] = 5e6
        _setup_db(mock_db, quotes, _make_indicators(), _make_stock())
        service = MultiAgentAnalysisService(mock_db)
        result = await service.analyze_stock("600519.SH")
        fund = result["fundamental"]
        assert any("流动性" in r for r in fund.get("reasons", []))


class TestCatalystAgent:
    async def test_continuous_up(self, mock_db):
        quotes = _make_quotes(30)
        for i in range(-3, 0):
            quotes[i]["pct_change"] = 2.5
        _setup_db(mock_db, quotes, _make_indicators(), _make_stock())
        service = MultiAgentAnalysisService(mock_db)
        result = await service.analyze_stock("600519.SH")
        cat = result["catalyst"]
        assert any("连续" in r for r in cat.get("reasons", [])) or cat["score"] > 40


class TestLLMDeepReport:
    async def test_fallback_when_no_llm(self, service):
        result = await service.analyze_stock("600519.SH")
        report = result["llm_deep_report"]
        assert report["source"] == "fallback"
        assert "核心观点" in report["raw"]
        assert isinstance(report["sections"], dict)

    async def test_llm_configured_calls_api(self, mock_db):
        _setup_db(mock_db, _make_quotes(), _make_indicators(), _make_stock(),
                   llm_config={"is_active": True, "api_key": "sk-test",
                               "base_url": "https://api.openai.com/v1", "model": "gpt-3.5-turbo"})
        service = MultiAgentAnalysisService(mock_db)
        with patch("openai.OpenAI") as mock_cls:
            mock_client = MagicMock()
            mock_choice = MagicMock()
            mock_msg = MagicMock()
            mock_msg.content = "## 核心观点\n测试报告内容\n## 技术面研判\n技术面良好"
            mock_choice.message = mock_msg
            mock_completion = MagicMock()
            mock_completion.choices = [mock_choice]
            mock_client.chat.completions.create = MagicMock(return_value=mock_completion)
            mock_cls.return_value = mock_client
            result = await service.analyze_stock("600519.SH")
            report = result["llm_deep_report"]
            assert report["source"] == "llm"
            assert "核心观点" in report["raw"]

    async def test_llm_timeout_fallback(self, mock_db):
        _setup_db(mock_db, _make_quotes(), _make_indicators(), _make_stock(),
                   llm_config={"is_active": True, "api_key": "sk-test",
                               "base_url": "https://api.openai.com/v1", "model": "gpt-3.5-turbo"})
        service = MultiAgentAnalysisService(mock_db)
        with patch("openai.OpenAI") as mock_cls:
            mock_client = MagicMock()
            mock_client.chat.completions.create = MagicMock(side_effect=aio.TimeoutError)
            mock_cls.return_value = mock_client
            result = await service.analyze_stock("600519.SH")
            report = result["llm_deep_report"]
            assert report["source"] == "fallback"


class TestScoreClamping:
    async def test_scores_within_bounds(self, service):
        result = await service.analyze_stock("600519.SH")
        for dim in ["technical", "fundamental", "catalyst"]:
            score = result[dim]["score"]
            assert 0 <= score <= 100
        assert 0 <= result["total_score"] <= 100


class TestIndustryWeights:
    def test_config_structure(self):
        assert "high_attention" in INDUSTRY_WEIGHTS
        assert "stable" in INDUSTRY_WEIGHTS
        assert "growth" in INDUSTRY_WEIGHTS
        assert isinstance(INDUSTRY_WEIGHTS["high_attention"], list)
        assert isinstance(INDUSTRY_WEIGHTS["high_attention_score"], int)
