"""
Scrapy下载中间件
"""
import random
import redis
from loguru import logger
from crawler.settings import REDIS_URL, PROXY_POOL_ENABLED, PROXY_POOL_REDIS_KEY


class RandomUserAgentMiddleware:
    """随机User-Agent中间件"""

    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ]

    def process_request(self, request, spider):
        ua = random.choice(self.USER_AGENTS)
        request.headers["User-Agent"] = ua


class ProxyMiddleware:
    """代理池中间件"""

    def __init__(self):
        self.redis_client = None
        self.proxy_enabled = PROXY_POOL_ENABLED

    def open_spider(self, spider):
        if self.proxy_enabled:
            self.redis_client = redis.from_url(REDIS_URL)

    def process_request(self, request, spider):
        if not self.proxy_enabled:
            return

        # 从代理池获取一个代理
        try:
            proxy = self._get_proxy()
            if proxy:
                request.meta["proxy"] = f"http://{proxy}"
        except Exception as e:
            logger.warning(f"获取代理失败: {e}")

    def process_response(self, request, response, spider):
        # 如果响应状态码是403/429等，标记代理不可用
        if response.status in [403, 429, 503]:
            proxy = request.meta.get("proxy")
            if proxy and self.redis_client:
                self._remove_proxy(proxy.replace("http://", ""))
        return response

    def process_exception(self, request, exception, spider):
        # 请求异常时移除代理
        proxy = request.meta.get("proxy")
        if proxy and self.redis_client:
            self._remove_proxy(proxy.replace("http://", ""))
        return None

    def _get_proxy(self):
        """从Redis有序集合获取一个代理"""
        if not self.redis_client:
            return None
        # 随机获取一个高分代理
        proxies = self.redis_client.zrevrange(PROXY_POOL_REDIS_KEY, 0, 9)
        if proxies:
            return random.choice(proxies).decode("utf-8")
        return None

    def _remove_proxy(self, proxy):
        """移除不可用代理"""
        if self.redis_client:
            self.redis_client.zrem(PROXY_POOL_REDIS_KEY, proxy)
