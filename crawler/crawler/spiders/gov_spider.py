"""
政府网站爬虫示例
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
            name="朝阳区政府官网",
            entry_url="https://www.bjchy.gov.cn/",
            source_type="gov",
            source_channel="朝阳区政府",
            area_scope=["chaoyang"],
            selector_config={
                "list_selector": ".news-list li",
                "title_selector": "a",
                "link_selector": "a@href",
                "date_selector": ".date",
                "content_selector": ".article-content",
                "next_page_selector": ".next-page a",
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
            name="海淀区政府官网",
            entry_url="https://www.bjhd.gov.cn/",
            source_type="gov",
            source_channel="海淀区政府",
            area_scope=["haidian"],
            selector_config={
                "list_selector": ".news-list li",
                "title_selector": "a",
                "link_selector": "a@href",
                "date_selector": ".date",
                "content_selector": ".article-content",
            },
            **kwargs,
        )
