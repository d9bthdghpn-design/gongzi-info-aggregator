"""
代理池工具
"""
import redis
import requests
from loguru import logger
from crawler.settings import REDIS_URL, PROXY_POOL_REDIS_KEY


class ProxyPool:
    """代理池管理（基于Redis有序集合，按质量分数排序）"""

    def __init__(self):
        self.redis = redis.from_url(REDIS_URL)
        self.key = PROXY_POOL_REDIS_KEY

    def get_proxy(self) -> str:
        """获取一个高分代理"""
        # 获取前10个高分代理，随机选一个
        proxies = self.redis.zrevrange(self.key, 0, 9)
        if proxies:
            import random
            return random.choice(proxies).decode("utf-8")
        return None

    def add_proxy(self, proxy: str, score: int = 100):
        """添加代理"""
        self.redis.zadd(self.key, {proxy: score})

    def update_score(self, proxy: str, delta: int):
        """更新代理分数"""
        self.redis.zincrby(self.key, delta, proxy)

    def remove_proxy(self, proxy: str):
        """移除代理"""
        self.redis.zrem(self.key, proxy)

    def get_all(self) -> list:
        """获取所有代理（按分数排序）"""
        return [p.decode("utf-8") for p in self.redis.zrevrange(self.key, 0, -1)]

    def count(self) -> int:
        """获取代理数量"""
        return self.redis.zcard(self.key)

    def check_proxy(self, proxy: str, test_url: str = "http://www.baidu.com") -> bool:
        """检测代理可用性"""
        try:
            response = requests.get(
                test_url,
                proxies={"http": f"http://{proxy}", "https": f"http://{proxy}"},
                timeout=10,
            )
            return response.status_code == 200
        except Exception:
            return False

    def refresh_from_api(self, api_url: str):
        """从代理API获取新代理"""
        try:
            response = requests.get(api_url, timeout=30)
            if response.status_code == 200:
                data = response.json()
                proxies = data.get("data", [])
                for proxy in proxies:
                    self.add_proxy(proxy)
                logger.info(f"从API获取 {len(proxies)} 个代理")
        except Exception as e:
            logger.error(f"从API获取代理失败: {e}")
