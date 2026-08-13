"""
Scrapy Item定义
"""
import scrapy


class NewsItem(scrapy.Item):
    """资讯Item"""
    title = scrapy.Field()           # 标题
    content_raw = scrapy.Field()     # 原始正文
    source_type = scrapy.Field()     # 来源类型: gov/park/enterprise/bidding
    source_channel = scrapy.Field()  # 来源渠道名称
    source_url = scrapy.Field()      # 原始URL
    publish_date = scrapy.Field()    # 发布日期
    area_tags = scrapy.Field()       # 区域标签
    industry_tags = scrapy.Field()   # 行业标签
    info_type = scrapy.Field()       # 资讯类型
    source_id = scrapy.Field()       # 采集源ID
    dedup_hash = scrapy.Field()      # 去重哈希
    crawl_time = scrapy.Field()      # 采集时间
