"""Recall AI 后端配置。

Args:
    env: 通过环境变量覆盖,参见 .env.example
Returns:
    Settings 单例
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置,支持 .env 覆盖。"""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # 应用
    APP_NAME: str = "Recall AI 智能错题本"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True

    # 数据库
    DATABASE_URL: str = "sqlite:///./recall.db"

    # ChromaDB 向量库
    CHROMA_DIR: str = "./chroma_data"
    CHROMA_COLLECTION: str = "questions"
    DEDUP_THRESHOLD: float = 0.95

    # DeepSeek API
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"
    AI_TIMEOUT_SECONDS: float = 60.0

    # 文件存储
    UPLOAD_DIR: str = "./uploads"

    # 复习计划默认值
    DAILY_REVIEW_LIMIT: int = 20
    BORED_DAYS: int = 7


@lru_cache
def get_settings() -> Settings:
    """获取配置单例(缓存,避免重复读取 .env)。"""
    return Settings()
