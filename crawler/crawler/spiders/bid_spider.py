"""
招投标平台爬虫
注意：选择器为初始配置，实际以 CrawlSource.selector_config 数据库配置为准。
"""
from crawler.spiders.base_spider import BaseConfigSpider


class CcgpSpider(BaseConfigSpider):
    """中国政府采购网爬虫（地方公告）"""

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
            area_tags=[],
            info_type="bidding",
            selector_config={
                "list_selector": ".vT-srch-result-list li, ul.vT-srch-result-list-bid li",
                "title_selector": "a",
                "link_selector": "a@href",
                "date_selector": ".date, span.time",
                "content_selector": ".vF_detail_main, .vF_detail_content",
                "next_page_selector": ".next a, a.next",
            },
            **kwargs,
        )


class CcgpBeijingSpider(BaseConfigSpider):
    """北京市政府采购网爬虫（区级公告）"""

    name = "ccgp_beijing"

    custom_settings = {
        "DOWNLOAD_DELAY": 3,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 2,
    }

    def __init__(self, **kwargs):
        super().__init__(
            name="北京市政府采购网",
            entry_url="http://www.ccgp-beijing.gov.cn/xxgg/qjxxgg/",
            source_type="bidding",
            source_channel="北京市政府采购网",
            area_tags=["chaoyang", "haidian"],
            info_type="bidding",
            selector_config={
                "list_selector": ".list li, ul.list li, .news-list li",
                "title_selector": "a",
                "link_selector": "a@href",
                "date_selector": ".date, span.time",
                "content_selector": ".article-content, .TRS_Editor, .content",
                "next_page_selector": ".next a, a.next",
            },
            **kwargs,
        )


class BiddingBeijingSpider(BaseConfigSpider):
    """北京市公共资源交易服务平台爬虫（域名已更正为 ggzyfw.beijing.gov.cn）"""

    name = "bidding_beijing"

    custom_settings = {
        "DOWNLOAD_DELAY": 2,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 2,
    }

    def __init__(self, **kwargs):
        super().__init__(
            name="北京市公共资源交易服务平台",
            entry_url="https://ggzyfw.beijing.gov.cn/",
            source_type="bidding",
            source_channel="北京市公共资源交易服务平台",
            area_tags=["chaoyang", "haidian", "fengtai"],
            info_type="bidding",
            selector_config={
                "list_selector": ".news-list li, .list li, .jyxx-list li",
                "title_selector": "a",
                "link_selector": "a@href",
                "date_selector": ".date, .time, span.date",
                "content_selector": ".article-content, .content, .detail-content",
                "next_page_selector": ".next a, a.next",
            },
            **kwargs,
        )
