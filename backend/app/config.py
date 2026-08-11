"""
对公资讯聚合系统 - 配置管理
"""
import os
from typing import Optional


class Settings:
    """应用配置"""
    # 应用配置
    APP_NAME: str = "对公资讯聚合系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    API_V1_PREFIX: str = "/api/v1"

    # 数据库配置 - 默认使用SQLite
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./gongzi_info.db"
    )
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # Redis配置
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    REDIS_CACHE_DB: int = 0
    REDIS_CELERY_DB: int = 1

    # JWT配置
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", os.getenv("SECRET_KEY", "gongzi-info-secret-key-change-in-production"))
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120  # 2小时
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Celery配置
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")

    # AI大模型配置
    AI_MODEL: str = os.getenv("AI_MODEL", "gpt-3.5-turbo")
    AI_API_KEY: str = os.getenv("AI_API_KEY", "")
    AI_BASE_URL: str = os.getenv("AI_BASE_URL", "")
    AI_MAX_TOKENS: int = 2000
    AI_TEMPERATURE: float = 0.3
    AI_BATCH_SIZE: int = 10

    # 采集配置
    CRAWL_USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    CRAWL_DELAY: float = 1.0
    PROXY_POOL_ENABLED: bool = False

    # SSO配置
    SSO_WECOM_ENABLED: bool = False
    SSO_WECOM_CORP_ID: str = ""
    SSO_WECOM_AGENT_ID: str = ""
    SSO_WECOM_SECRET: str = ""
    SSO_FEISHU_ENABLED: bool = False
    SSO_FEISHU_APP_ID: str = ""
    SSO_FEISHU_APP_SECRET: str = ""

    # 安全配置
    IP_WHITELIST_ENABLED: bool = False
    IP_WHITELIST: list = []
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "*").split(",") if os.getenv("CORS_ORIGINS") else ["*"]

    # 分页配置
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100


settings = Settings()
