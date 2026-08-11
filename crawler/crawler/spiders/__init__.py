"""
爬虫模块
"""
from crawler.spiders.base_spider import BaseConfigSpider
from crawler.spiders.gov_spider import GovChaoyangSpider, GovHaidianSpider
from crawler.spiders.bid_spider import CcgpSpider, BiddingBeijingSpider

__all__ = [
    "BaseConfigSpider",
    "GovChaoyangSpider",
    "GovHaidianSpider",
    "CcgpSpider",
    "BiddingBeijingSpider",
]
