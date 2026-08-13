"""
基础爬虫类 - 配置化爬虫基类
通过 CrawlSource.selector_config 配置来解析不同网站，无需写代码
"""
import re

import scrapy
from bs4 import BeautifulSoup
from loguru import logger
from urllib.parse import urljoin

from crawler.items import NewsItem

# 日期正则：匹配 2026-08-12、2026/08/12、2026年08月12日、2026-08-12 16:12 等
DATE_PATTERN = re.compile(
    r"(\d{4}[-/年.]\d{1,2}[-/月.]\d{1,2}(?:日)?(?:\s+\d{1,2}:\d{2}(?::\d{2})?)?)"
)


def _extract_date(text):
    """从文本中正则提取日期字符串"""
    if not text:
        return ""
    m = DATE_PATTERN.search(text)
    return m.group(1) if m else ""


class BaseConfigSpider(scrapy.Spider):
    """
    配置化基础爬虫类
    selector_config 支持的字段：
      - list_selector: 列表项选择器（CSS），支持逗号分隔多个备选
      - title_selector: 标题选择器（相对于列表项），默认 a
      - link_selector: 链接选择器，格式 "selector@attr"（默认 a@href）
      - date_selector: 日期选择器（相对于列表项）
      - date_regex: 选择器取不到时是否用正则从列表项文本兜底（默认 true）
      - content_selector: 详情页正文选择器，支持逗号分隔多个备选
      - next_page_selector: 下一页链接选择器
      - encoding: 页面编码（默认 utf-8）
    """

    name = "base_config"

    def __init__(self, source_id=None, name=None, entry_url=None,
                 source_type="gov", source_channel="", selector_config=None,
                 area_tags=None, industry_tags=None, info_type="", **kwargs):
        super().__init__(**kwargs)
        self.source_id = source_id
        self.source_name = name
        self.entry_url = entry_url
        self.source_type = source_type
        self.source_channel = source_channel
        self.selector_config = selector_config or {}
        self.area_tags = area_tags or []
        self.industry_tags = industry_tags or []
        self.info_type = info_type

    def start_requests(self):
        if self.entry_url:
            yield scrapy.Request(
                self.entry_url,
                callback=self.parse_list,
                meta={"source_id": self.source_id},
            )

    @staticmethod
    def _css_first_text(item, selectors):
        """依次尝试多个CSS选择器（逗号分隔），返回第一个非空文本"""
        if isinstance(selectors, str):
            selectors = [s.strip() for s in selectors.split(",")]
        for sel in selectors:
            if not sel:
                continue
            text = item.css(sel + "::text").get()
            if not text:
                text = item.css(sel + " ::text").get()
            if text and text.strip():
                return text.strip()
        return ""

    def parse_list(self, response):
        """解析列表页"""
        config = self.selector_config
        list_selector = config.get("list_selector", "")
        title_selector = config.get("title_selector", "a")
        link_selector = config.get("link_selector", "a@href")
        date_selector = config.get("date_selector", "")
        use_date_regex = config.get("date_regex", True)

        if not list_selector:
            logger.warning(f"未配置列表选择器: {self.source_name}")
            return

        items = response.css(list_selector)
        logger.info(f"列表页获取到 {len(items)} 条记录: {self.source_name}")

        # 解析链接选择器
        link_attr = "href"
        link_sel = link_selector
        if "@" in link_selector:
            link_sel, link_attr = link_selector.split("@", 1)

        for item in items:
            try:
                # 提取标题：优先链接的 title 属性，再选选择器文本
                title = ""
                title_attr = item.css(link_sel).attrib.get("title", "")
                if title_attr:
                    title = title_attr.strip()
                if not title:
                    title = self._css_first_text(item, title_selector)
                # 清理标题中可能残留的 HTML 标签
                title = re.sub(r"<[^>]+>", "", title).strip()

                if not title:
                    continue

                # 提取链接
                link = item.css(link_sel).attrib.get(link_attr, "")
                if link:
                    link = urljoin(response.url, link.strip())

                # 提取日期：先选择器，再正则兜底
                publish_date = ""
                if date_selector:
                    publish_date = self._css_first_text(item, date_selector)
                if publish_date:
                    publish_date = _extract_date(publish_date)
                if not publish_date and use_date_regex:
                    item_text = " ".join(item.css("::text").getall())
                    publish_date = _extract_date(item_text)

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

        # 翻页
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
            content = ""
            # 支持逗号分隔多个正文选择器，依次尝试
            selectors = [s.strip() for s in content_selector.split(",") if s.strip()]
            for sel in selectors:
                content_elem = response.css(sel)
                if content_elem:
                    parts = content_elem.css("::text").getall()
                    content = "\n".join([p.strip() for p in parts if p.strip()])
                    if len(content) >= 50:
                        break

            # BeautifulSoup 兜底
            if not content or len(content) < 50:
                soup = BeautifulSoup(response.text, "lxml")
                fallback = selectors + [
                    ".article-content", ".content", "#content", ".detail",
                    ".news-content", ".TRS_Editor", ".article", "article",
                    ".vF_detail_content", ".con", ".view", "#zoom",
                ]
                for selector in fallback:
                    elem = soup.select_one(selector)
                    if elem:
                        for tag in elem.find_all(["script", "style"]):
                            tag.decompose()
                        content = elem.get_text(strip=False, separator="\n")
                        content = "\n".join(
                            line.strip() for line in content.splitlines() if line.strip()
                        )
                        if len(content) >= 50:
                            break

            item = NewsItem()
            item["title"] = title
            item["content_raw"] = content
            item["source_type"] = self.source_type
            item["source_channel"] = self.source_channel or self.source_name
            item["source_url"] = source_url
            item["publish_date"] = publish_date
            item["area_tags"] = self.area_tags
            item["industry_tags"] = self.industry_tags
            item["info_type"] = self.info_type
            item["source_id"] = self.source_id

            yield item

        except Exception as e:
            logger.error(f"解析详情页失败: {source_url}, {e}")
