"""
Scrapy配置
"""
import os
from dotenv import load_dotenv

load_dotenv()

BOT_NAME = "gongzi_crawler"

SPIDER_MODULES = ["crawler.spiders"]
NEWSPIDER_MODULE = "crawler.spiders"

# 遵守robots.txt（政府站通常允许，如个别站禁止可在 spider 中覆盖）
ROBOTSTXT_OBEY = True

# 并发请求数（政府站调低，避免被封）
CONCURRENT_REQUESTS = 8
CONCURRENT_REQUESTS_PER_DOMAIN = 2

# 下载延迟
DOWNLOAD_DELAY = float(os.getenv("CRAWL_DELAY", "2.0"))
RANDOMIZE_DOWNLOAD_DELAY = True

# 禁用Cookie
COOKIES_ENABLED = False

# 默认请求头
DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "User-Agent": os.getenv(
        "CRAWL_USER_AGENT",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ),
}

# 下载中间件
DOWNLOADER_MIDDLEWARES = {
    "crawler.middlewares.RandomUserAgentMiddleware": 400,
    "crawler.middlewares.ProxyMiddleware": 500,
    "scrapy.downloadermiddlewares.retry.RetryMiddleware": 550,
}

# 管道
ITEM_PIPELINES = {
    "crawler.pipelines.DedupPipeline": 100,   # 去重
    "crawler.pipelines.CleanPipeline": 200,   # 清洗
    "crawler.pipelines.DatabasePipeline": 300,  # 入库
}

# 重试设置
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]

# 下载超时
DOWNLOAD_TIMEOUT = 30

# 自动限速
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 2
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0

# HTTP缓存（开发用）
HTTPCACHE_ENABLED = False
HTTPCACHE_EXPIRATION_SECS = 3600
HTTPCACHE_DIR = "httpcache"

# 日志
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s [%(name)s] %(levelname)s: %(message)s"

# Redis配置（去重队列，可选）
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# 数据库配置
# SQLAlchemy 格式（给后端用）
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./gongzi_info.db")


def _get_psycopg2_dsn() -> str:
    """将 SQLAlchemy 格式的 DATABASE_URL 转为 psycopg2 可识别的 DSN"""
    url = DATABASE_URL
    if url.startswith("postgresql+"):
        # postgresql+psycopg2://user:pass@host:port/dbname → postgresql://user:pass@host:port/dbname
        url = "postgresql://" + url.split("://", 1)[1]
    if url.startswith("sqlite"):
        # SQLite 不被 psycopg2 支持，返回空，Pipeline 会走 SQLAlchemy 路线
        return ""
    return url


# psycopg2 原生 DSN（给爬虫 Pipeline 用）
PSYCOPG2_DSN = _get_psycopg2_dsn()

# 代理池配置
PROXY_POOL_ENABLED = os.getenv("PROXY_POOL_ENABLED", "false").lower() == "true"
PROXY_POOL_REDIS_KEY = "crawler:proxy_pool"

# 去重配置
DEDUP_REDIS_SET = "crawler:dedup:urls"
DEDUP_HASH_REDIS_SET = "crawler:dedup:hashes"
