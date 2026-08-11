"""
去重工具
"""
import hashlib
import redis
from crawler.settings import REDIS_URL, DEDUP_REDIS_SET, DEDUP_HASH_REDIS_SET


class URLDeduplicator:
    """URL去重器（Redis集合）"""

    def __init__(self):
        self.redis = redis.from_url(REDIS_URL)
        self.key = DEDUP_REDIS_SET

    def is_duplicate(self, url: str) -> bool:
        """检查URL是否重复"""
        return self.redis.sismember(self.key, url)

    def add(self, url: str):
        """添加URL到去重集合"""
        self.redis.sadd(self.key, url)

    def count(self) -> int:
        """获取集合大小"""
        return self.redis.scard(self.key)


class ContentDeduplicator:
    """内容去重器（基于MD5哈希）"""

    def __init__(self):
        self.redis = redis.from_url(REDIS_URL)
        self.key = DEDUP_HASH_REDIS_SET

    @staticmethod
    def compute_hash(title: str, content: str) -> str:
        """计算内容哈希"""
        text = title + (content[:500] if content else "")
        return hashlib.md5(text.encode("utf-8")).hexdigest()

    def is_duplicate(self, dedup_hash: str) -> bool:
        """检查内容是否重复"""
        return self.redis.sismember(self.key, dedup_hash)

    def add(self, dedup_hash: str):
        """添加内容哈希到去重集合"""
        self.redis.sadd(self.key, dedup_hash)

    def count(self) -> int:
        """获取集合大小"""
        return self.redis.scard(self.key)
