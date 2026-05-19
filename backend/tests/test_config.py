import pytest
from app.core.config import Settings


class TestSettings:
    def test_default_values(self, monkeypatch):
        monkeypatch.delenv("DEBUG", raising=False)
        monkeypatch.delenv("MONGO_URI", raising=False)
        monkeypatch.delenv("MONGO_DB", raising=False)
        s = Settings(
            TUSHARE_TOKEN="",
            LLM_API_KEY="",
            JWT_SECRET="test-secret-for-unit-test",
            _env_file=None,
        )
        assert s.APP_NAME == "A股行情分析平台"
        assert s.DEBUG is False
        assert s.MONGO_URI == "mongodb://localhost:27017"
        assert s.MONGO_DB == "stock_analysis"
        assert s.MONGO_MAX_POOL == 50
        assert s.REDIS_URL == "redis://localhost:6379/0"
        assert s.REDIS_MAX_CONNECTIONS == 100
        assert s.AKSHARE_ENABLED is True
        assert s.LLM_BASE_URL == ""
        assert s.LLM_MODEL == ""
        assert s.CORS_ORIGINS == ["http://localhost:5173", "http://localhost:3000"]
        assert s.REALTIME_INTERVAL_SEC == 3
        assert s.DAILY_SYNC_HOUR == 15
        assert s.JWT_EXPIRE_HOURS == 24

    def test_env_override(self, monkeypatch):
        monkeypatch.setenv("MONGO_URI", "mongodb://custom:27017")
        monkeypatch.setenv("MONGO_DB", "test_db")
        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("JWT_SECRET", "my-secret")
        s = Settings(_env_file=None)
        assert s.MONGO_URI == "mongodb://custom:27017"
        assert s.MONGO_DB == "test_db"
        assert s.DEBUG is True
        assert s.JWT_SECRET == "my-secret"
