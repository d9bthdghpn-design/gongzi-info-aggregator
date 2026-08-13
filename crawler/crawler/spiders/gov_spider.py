"""
政府网站爬虫
注意：选择器为初始配置，实际以 CrawlSource.selector_config 数据库配置为准。
如选择器不匹配，可通过数据源管理页面调整，无需改代码。
"""
from crawler.spiders.base_spider import BaseConfigSpider


class GovChaoyangSpider(BaseConfigSpider):
    """朝阳区政府网站爬虫"""

    name = "gov_chaoyang"

    custom_settings = {
        "DOWNLOAD_DELAY": 2,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 2,
    }

    def __init__(self, **kwargs):
        super().__init__(
            name="朝阳区政府",
            entry_url="https://www.bjchy.gov.cn/",
            source_type="gov",
            source_channel="朝阳区政府",
            area_tags=["chaoyang"],
            selector_config={
                "list_selector": ".news-list li, .list li, ul.list li",
                "title_selector": "a",
                "link_selector": "a@href",
                "date_selector": ".date, .time, span.date",
                "content_selector": ".article-content, .TRS_Editor, .content, #content",
                "next_page_selector": ".next-page a, .next a",
            },
            **kwargs,
        )


class GovHaidianSpider(BaseConfigSpider):
    """海淀区政府网站爬虫"""

    name = "gov_haidian"

    custom_settings = {
        "DOWNLOAD_DELAY": 2,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 2,
    }

    def __init__(self, **kwargs):
        super().__init__(
            name="海淀区政府",
            entry_url="https://www.bjhd.gov.cn/",
            source_type="gov",
            source_channel="海淀区政府",
            area_tags=["haidian"],
            selector_config={
                "list_selector": ".news-list li, .list li, ul.list li",
                "title_selector": "a",
                "link_selector": "a@href",
                "date_selector": ".date, .time, span.date",
                "content_selector": ".article-content, .TRS_Editor, .content, #content",
            },
            **kwargs,
        )
