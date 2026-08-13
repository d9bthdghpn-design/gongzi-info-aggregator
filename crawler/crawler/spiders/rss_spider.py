"""
RSS/Atom 爬虫 - 最稳定的采集方式，无需维护 CSS 选择器
"""
import hashlib
from datetime import datetime
from loguru import logger

try:
    import feedparser
    HAS_FEEDPARSER = True
except ImportError:
    HAS_FEEDPARSER = False

import scrapy
from crawler.items import NewsItem


class RssSpider(scrapy.Spider):
    """
    RSS/Atom 通用爬虫
    参数：
      - feed_url: RSS/Atom 订阅地址
      - source_name: 来源名称
      - source_type: 来源类型
      - source_channel: 来源渠道
      - area_tags: 区域标签列表
      - industry_tags: 行业标签列表
      - info_type: 资讯类型
      - source_id: 采集源 ID
    """

    name = "rss"

    def __init__(self, feed_url=None, source_name="", source_type="gov",
                 source_channel="", area_tags=None, industry_tags=None,
                 info_type="", source_id=None, max_items=30, **kwargs):
        super().__init__(**kwargs)
        self.feed_url = feed_url
        self.source_name = source_name
        self.source_type = source_type
        self.source_channel = source_channel or source_name
        self.area_tags = area_tags or []
        self.industry_tags = industry_tags or []
        self.info_type = info_type
        self.source_id = source_id
        self.max_items = int(max_items)

        if feed_url:
            self.start_urls = [feed_url]

    def parse(self, response):
        if not HAS_FEEDPARSER:
            logger.error("feedparser 未安装，请 pip install feedparser")
            return

        feed = feedparser.parse(response.body)

        if feed.bozo and not feed.entries:
            logger.warning(f"RSS 解析异常: {self.source_name} - {feed.bozo_exception}")
            return

        logger.info(f"RSS 获取到 {len(feed.entries)} 条: {self.source_name}")

        for entry in feed.entries[:self.max_items]:
            try:
                title = entry.get("title", "").strip()
                link = entry.get("link", "").strip()
                if not title or not link:
                    continue

                # 发布日期
                publish_date = ""
                for date_field in ["published_parsed", "updated_parsed", "created_parsed"]:
                    parsed = entry.get(date_field)
                    if parsed:
                        try:
                            publish_date = datetime(*parsed[:6]).date()
                        except Exception:
                            pass
                        break

                # 正文：优先 content，其次 summary
                content = ""
                if entry.get("content"):
                    content = entry["content"][0].get("value", "")
                elif entry.get("summary"):
                    content = entry["summary"]

                # 去 HTML 标签
                if content:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(content, "lxml")
                    content = soup.get_text(separator="\n")
                    content = "\n".join(
                        line.strip() for line in content.splitlines() if line.strip()
                    )

                item = NewsItem()
                item["title"] = title
                item["content_raw"] = content
                item["source_type"] = self.source_type
                item["source_channel"] = self.source_channel
                item["source_url"] = link
                item["publish_date"] = publish_date
                item["area_tags"] = self.area_tags
                item["industry_tags"] = self.industry_tags
                item["info_type"] = self.info_type
                item["source_id"] = self.source_id

                yield item

            except Exception as e:
                logger.error(f"解析 RSS 条目失败: {e}")
                continue
