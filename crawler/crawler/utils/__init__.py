"""
工具模块
"""
from crawler.utils.dedup import URLDeduplicator, ContentDeduplicator
from crawler.utils.proxy import ProxyPool

__all__ = ["URLDeduplicator", "ContentDeduplicator", "ProxyPool"]
