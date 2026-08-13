"""
对公资讯聚合系统 - 配置管理
"""
import os
import logging

logger = logging.getLogger(__name__)


def _get_bool(name: str, default: bool = False) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.lower() in ("1", "true", "yes", "on")


def _get_list(name: str, default: list) -> list:
    val = os.getenv(name)
    if not val:
        return default
    return [item.strip() for item in val.split(",") if item.strip()]


class Settings:
    """应用配置"""
    # 应用配置
    APP_NAME: str = "对公资讯聚合系统"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = _get_bool("DEBUG", False)
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")  # development / production
    API_V1_PREFIX: str = "/api/v1"

    # 数据库配置 - 默认使用SQLite
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./gongzi_info.db")
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # Redis配置
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    REDIS_CACHE_DB: int = 0
    REDIS_CELERY_DB: int = 1

    # JWT配置
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", os.getenv("SECRET_KEY", "gongzi-info-secret-key-change-in-production"))
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    # Celery配置
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")

    # AI大模型配置
    AI_MODEL: str = os.getenv("AI_MODEL", "gpt-3.5-turbo")
    AI_API_KEY: str = os.getenv("AI_API_KEY", "")
    AI_BASE_URL: str = os.getenv("AI_BASE_URL", "")
    AI_MAX_TOKENS: int = int(os.getenv("AI_MAX_TOKENS", "2000"))
    AI_TEMPERATURE: float = float(os.getenv("AI_TEMPERATURE", "0.3"))
    AI_BATCH_SIZE: int = 10
    # AI 处理后自动发布的最低质量分（低于此分进待审核）
    AI_AUTO_PUBLISH_SCORE: int = int(os.getenv("AI_AUTO_PUBLISH_SCORE", "60"))
    # 高价值商机即时推送阈值
    HIGH_VALUE_SCORE: int = int(os.getenv("HIGH_VALUE_SCORE", "80"))

    # 采集配置
    CRAWL_USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    CRAWL_DELAY: float = 1.0
    PROXY_POOL_ENABLED: bool = _get_bool("PROXY_POOL_ENABLED", False)

    # 推送配置 - 飞书/企微机器人 Webhook
    FEISHU_WEBHOOK_URL: str = os.getenv("FEISHU_WEBHOOK_URL", "")
    FEISHU_WEBHOOK_SECRET: str = os.getenv("FEISHU_WEBHOOK_SECRET", "")
    WECOM_WEBHOOK_URL: str = os.getenv("WECOM_WEBHOOK_URL", "")
    WECOM_WEBHOOK_SECRET: str = os.getenv("WECOM_WEBHOOK_SECRET", "")
    # 每日简报推送时间（24小时制）
    BRIEFING_PUSH_HOUR: int = int(os.getenv("BRIEFING_PUSH_HOUR", "7"))
    BRIEFING_PUSH_MINUTE: int = int(os.getenv("BRIEFING_PUSH_MINUTE", "30"))

    # SSO配置
    SSO_WECOM_ENABLED: bool = _get_bool("SSO_WECOM_ENABLED", False)
    SSO_WECOM_CORP_ID: str = os.getenv("SSO_WECOM_CORP_ID", "")
    SSO_WECOM_AGENT_ID: str = os.getenv("SSO_WECOM_AGENT_ID", "")
    SSO_WECOM_SECRET: str = os.getenv("SSO_WECOM_SECRET", "")
    SSO_FEISHU_ENABLED: bool = _get_bool("SSO_FEISHU_ENABLED", False)
    SSO_FEISHU_APP_ID: str = os.getenv("SSO_FEISHU_APP_ID", "")
    SSO_FEISHU_APP_SECRET: str = os.getenv("SSO_FEISHU_APP_SECRET", "")

    # 安全配置
    IP_WHITELIST_ENABLED: bool = _get_bool("IP_WHITELIST_ENABLED", False)
    IP_WHITELIST: list = _get_list("IP_WHITELIST", [])
    CORS_ORIGINS: list = _get_list(
        "CORS_ORIGINS",
        ["http://localhost:8080", "http://localhost:5173", "http://127.0.0.1:8080"],
    )

    # 分页配置
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    def __init__(self):
        self._validate_security()

    def _validate_security(self):
        """生产环境安全校验"""
        if self.ENVIRONMENT == "production":
            if self.JWT_SECRET_KEY == "gongzi-info-secret-key-change-in-production":
                raise RuntimeError(
                    "生产环境必须设置 JWT_SECRET_KEY 环境变量，不能使用默认弱密钥"
                )
            if "*" in self.CORS_ORIGINS:
                raise RuntimeError("生产环境 CORS_ORIGINS 不能使用通配符 *")
        else:
            if self.JWT_SECRET_KEY == "gongzi-info-secret-key-change-in-production":
                logger.warning("使用默认 JWT 密钥，仅限开发环境，生产环境请设置 JWT_SECRET_KEY")


settings = Settings()
