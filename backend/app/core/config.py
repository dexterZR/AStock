from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    DEBUG: bool = False
    APP_NAME: str = "A股行情分析平台"

    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB: str = "stock_analysis"
    MONGO_MAX_POOL: int = 50

    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_MAX_CONNECTIONS: int = 100

    TUSHARE_TOKEN: str = ""
    AKSHARE_ENABLED: bool = True

    MINIMAX_API_KEY: str = ""
    MINIMAX_BASE_URL: str = "https://api.minimax.chat/v1"
    MINIMAX_MODEL: str = "MiniMax-M2.7"

    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    REALTIME_INTERVAL_SEC: int = 3
    DAILY_SYNC_HOUR: int = 15

    JWT_SECRET: str = "change-me-in-production"
    JWT_EXPIRE_HOURS: int = 24

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


    def model_post_init(self, __context):
        if self.JWT_SECRET == "change-me-in-production":
            import warnings
            warnings.warn("\n⚠️  JWT_SECRET 使用默认值，生产环境请立即修改 .env 中的 JWT_SECRET！\n", stacklevel=2)

settings = Settings()
