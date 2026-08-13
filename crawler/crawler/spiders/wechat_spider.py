"""
微信公众号文章爬虫
解析 mp.weixin.qq.com/s/xxx 文章页面，提取标题、作者、发布时间、正文。

发现机制说明：
- 微信公众号没有公开的文章列表API，发现新文章有以下途径：
  1. RSSHub (https://docs.rsshub.app/) 部分公众号可生成RSS，走 rss 爬虫
  2. 搜狗微信搜索 (weixin.sogou.com) 有反爬，需浏览器渲染
  3. 手动提交文章URL（推荐MVP方案）
  4. 第三方付费API（如新榜、清博）
- 本爬虫只负责解析已知URL的文章页，不负责发现。
"""
import re

import scrapy
from bs4 import BeautifulSoup
from loguru import logger
from urllib.parse import urljoin

from crawler.items import NewsItem


class WechatSpider(scrapy.Spider):
    """微信公众号文章解析爬虫"""

    name = "wechat"

    # 微信文章页固定选择器
    TITLE_SELECTOR = "#activity-name, h1.rich_media_title, .rich_media_title"
    AUTHOR_SELECTOR = "#js_name, .rich_media_meta_text, #meta_content"
    DATE_SELECTOR = "#publish_time, .rich_media_meta_text"
    CONTENT_SELECTOR = "#js_content, .rich_media_content"

    def __init__(self, source_id=None, name=None, article_urls=None,
                 source_type="wechat", source_channel="",
                 area_tags=None, industry_tags=None, info_type="wechat",
                 **kwargs):
        super().__init__(**kwargs)
        self.source_id = source_id
        self.source_name = name or "微信公众号"
        self.source_type = source_type
        self.source_channel = source_channel or self.source_name
        self.area_tags = area_tags or []
        self.industry_tags = industry_tags or []
        self.info_type = info_type
        # article_urls 可以是逗号分隔的URL列表，或单个URL
        if isinstance(article_urls, str):
            self.article_urls = [u.strip() for u in article_urls.split(",") if u.strip()]
        else:
            self.article_urls = article_urls or []

    def start_requests(self):
        for url in self.article_urls:
            if "mp.weixin.qq.com" in url:
                yield scrapy.Request(
                    url,
                    callback=self.parse_article,
                    meta={"source_id": self.source_id, "source_url": url},
                )
            else:
                logger.warning(f"非微信文章链接，跳过: {url}")

    def parse_article(self, response):
        """解析微信文章页"""
        source_url = response.meta.get("source_url", response.url)

        try:
            # 标题
            title = ""
            for sel in self.TITLE_SELECTOR.split(","):
                text = response.css(sel.strip() + "::text").get()
                if text and text.strip():
                    title = text.strip()
                    break
            if not title:
                title = response.css("title::text").get("").strip()

            # 作者/公众号名
            author = ""
            for sel in self.AUTHOR_SELECTOR.split(","):
                text = response.css(sel.strip() + "::text").get()
                if text and text.strip():
                    author = text.strip()
                    break

            # 发布时间
            publish_date = ""
            date_text = response.css("#publish_time::text").get("")
            if not date_text:
                # 从页面JS变量中提取
                m = re.search(r'var\s+ct\s*=\s*"(\d+)"', response.text)
                if m:
                    from datetime import datetime
                    publish_date = datetime.fromtimestamp(int(m.group(1))).strftime("%Y-%m-%d")
            else:
                publish_date = date_text.strip()

            # 正文
            content = ""
            content_elem = response.css(self.CONTENT_SELECTOR)
            if content_elem:
                # 用 BeautifulSoup 提取纯文本，保留段落
                html_content = content_elem.get()
                soup = BeautifulSoup(html_content, "lxml")
                for tag in soup.find_all(["script", "style"]):
                    tag.decompose()
                # 移除图片data-src属性中的内容，保留alt
                for img in soup.find_all("img"):
                    alt = img.get("alt", "")
                    img.replace_with(f"[图片: {alt}]" if alt else "[图片]")
                content = soup.get_text(strip=False, separator="\n")
                content = "\n".join(
                    line.strip() for line in content.splitlines() if line.strip()
                )

            if not title:
                logger.warning(f"无法提取标题，跳过: {source_url}")
                return

            item = NewsItem()
            item["title"] = title
            item["content_raw"] = content
            item["source_type"] = self.source_type
            item["source_channel"] = f"{self.source_channel} - {author}" if author else self.source_channel
            item["source_url"] = source_url
            item["publish_date"] = publish_date
            item["area_tags"] = self.area_tags
            item["industry_tags"] = self.industry_tags
            item["info_type"] = self.info_type
            item["source_id"] = self.source_id

            yield item

        except Exception as e:
            logger.error(f"解析微信文章失败: {source_url}, {e}")
