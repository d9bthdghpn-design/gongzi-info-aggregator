"""
招投标平台爬虫示例
"""
from crawler.spiders.base_spider import BaseConfigSpider


class CcgpSpider(BaseConfigSpider):
    """中国政府采购网爬虫"""

    name = "ccgp"

    custom_settings = {
        "DOWNLOAD_DELAY": 3,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 2,
    }

    def __init__(self, **kwargs):
        super().__init__(
            name="中国政府采购网",
            entry_url="http://www.ccgp.gov.cn/cggg/dfgg/",
            source_type="bidding",
            source_channel="中国政府采购网",
            area_scope=[],
            selector_config={
                "list_selector": ".vT-srch-result-list li",
                "title_selector": "a",
                "link_selector": "a@href",
                "date_selector": ".date",
                "content_selector": ".vF_detail_main",
                "next_page_selector": ".next a",
            },
            **kwargs,
        )


class BiddingBeijingSpider(BaseConfigSpider):
    """北京市公共资源交易平台爬虫"""

    name = "bidding_beijing"

    custom_settings = {
        "DOWNLOAD_DELAY": 2,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 2,
    }

    def __init__(self, **kwargs):
        super().__init__(
            name="北京市公共资源交易平台",
            entry_url="https://ggzy.beijing.gov.cn/",
            source_type="bidding",
            source_channel="北京市公共资源交易平台",
            area_scope=["chaoyang", "haidian", "fengtai"],
            selector_config={
                "list_selector": ".news-list li",
                "title_selector": "a",
                "link_selector": "a@href",
                "date_selector": ".date",
                "content_selector": ".article-content",
            },
            **kwargs,
        )
