"""
基础爬虫类 - 配置化爬虫基类
"""
import scrapy
from bs4 import BeautifulSoup
from datetime import datetime
from loguru import logger
from urllib.parse import urljoin

from crawler.items import NewsItem


class BaseConfigSpider(scrapy.Spider):
    """
    配置化基础爬虫类
    通过selector_config配置来解析不同网站，无需写代码
    """

    name = "base_config"

    def __init__(self, source_id=None, name=None, entry_url=None,
                 source_type="gov", source_channel="", selector_config=None,
                 area_scope=None, industry_scope=None, **kwargs):
        super().__init__(**kwargs)
        self.source_id = source_id
        self.source_name = name
        self.entry_url = entry_url
        self.source_type = source_type
        self.source_channel = source_channel
        self.selector_config = selector_config or {}
        self.area_scope = area_scope or []
        self.industry_scope = industry_scope or []

    def start_requests(self):
        if self.entry_url:
            yield scrapy.Request(
                self.entry_url,
                callback=self.parse_list,
                meta={"source_id": self.source_id},
            )

    def parse_list(self, response):
        """解析列表页"""
        config = self.selector_config
        list_selector = config.get("list_selector", "")
        title_selector = config.get("title_selector", "a")
        link_selector = config.get("link_selector", "a@href")
        date_selector = config.get("date_selector", "")

        if not list_selector:
            logger.warning(f"未配置列表选择器: {self.source_name}")
            return

        items = response.css(list_selector)
        logger.info(f"列表页获取到 {len(items)} 条记录: {self.source_name}")

        for item in items:
            try:
                # 提取标题
                title = item.css(title_selector + "::text").get()
                if not title:
                    title = item.css(title_selector + " ::text").get()
                title = title.strip() if title else ""

                if not title:
                    continue

                # 提取链接
                link_attr = "href"
                if "@" in link_selector:
                    link_sel, link_attr = link_selector.split("@")
                else:
                    link_sel = link_selector

                link = item.css(link_sel).attrib.get(link_attr, "")
                if link:
                    link = urljoin(response.url, link)

                # 提取日期
                publish_date = ""
                if date_selector:
                    publish_date = item.css(date_selector + "::text").get()
                    if publish_date:
                        publish_date = publish_date.strip()

                # 构造详情页请求
                if link:
                    yield scrapy.Request(
                        link,
                        callback=self.parse_detail,
                        meta={
                            "title": title,
                            "publish_date": publish_date,
                            "source_url": link,
                            "source_id": self.source_id,
                        },
                    )

            except Exception as e:
                logger.error(f"解析列表项失败: {e}")
                continue

        # 翻页（如果配置了下一页选择器）
        next_page_selector = config.get("next_page_selector", "")
        if next_page_selector:
            next_page = response.css(next_page_selector).attrib.get("href", "")
            if next_page:
                next_page = urljoin(response.url, next_page)
                yield scrapy.Request(
                    next_page,
                    callback=self.parse_list,
                    meta={"source_id": self.source_id},
                )

    def parse_detail(self, response):
        """解析详情页"""
        config = self.selector_config
        content_selector = config.get("content_selector", ".article-content")

        title = response.meta.get("title", "")
        publish_date = response.meta.get("publish_date", "")
        source_url = response.meta.get("source_url", "")

        try:
            # 提取正文
            content = ""
            content_elem = response.css(content_selector)
            if content_elem:
                content = content_elem.css("::text").getall()
                content = "\n".join([p.strip() for p in content if p.strip()])

            # 如果CSS选择器没取到，用BeautifulSoup兜底
            if not content:
                soup = BeautifulSoup(response.text, "lxml")
                # 尝试常见的正文容器
                for selector in [".article-content", ".content", "#content", ".detail", ".news-content"]:
                    elem = soup.select_one(selector)
                    if elem:
                        content = elem.get_text(strip=False, separator="\n")
                        break

            # 构造Item
            item = NewsItem()
            item["title"] = title
            item["content_raw"] = content
            item["source_type"] = self.source_type
            item["source_channel"] = self.source_channel or self.source_name
            item["source_url"] = source_url
            item["publish_date"] = publish_date
            item["area_scope"] = self.area_scope
            item["industry_scope"] = self.industry_scope
            item["source_id"] = self.source_id

            yield item

        except Exception as e:
            logger.error(f"解析详情页失败: {source_url}, {e}")
