"""
Scrapy管道 - 去重、清洗、入库
"""
import hashlib
import json
import re
from datetime import datetime
from loguru import logger
import redis
import psycopg2
from psycopg2.extras import Json
from itemadapter import ItemAdapter

from crawler.settings import REDIS_URL, DATABASE_URL, DEDUP_REDIS_SET, DEDUP_HASH_REDIS_SET


class DedupPipeline:
    """去重管道（L1 URL去重 + L2 内容去重）"""

    def __init__(self):
        self.redis_client = None

    def open_spider(self, spider):
        self.redis_client = redis.from_url(REDIS_URL)

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        source_url = adapter.get("source_url")
        title = adapter.get("title", "")
        content = adapter.get("content_raw", "")

        # L1: URL去重
        if source_url:
            if self.redis_client.sismember(DEDUP_REDIS_SET, source_url):
                spider.crawler.stats.inc_value("dedup/url_duplicate")
                raise DropItem(f"URL重复: {source_url}")
            self.redis_client.sadd(DEDUP_REDIS_SET, source_url)

        # L2: 内容去重（标题+正文前500字MD5）
        if title and content:
            dedup_text = title + (content[:500] if content else "")
            dedup_hash = hashlib.md5(dedup_text.encode("utf-8")).hexdigest()
            adapter["dedup_hash"] = dedup_hash

            if self.redis_client.sismember(DEDUP_HASH_REDIS_SET, dedup_hash):
                spider.crawler.stats.inc_value("dedup/content_duplicate")
                raise DropItem(f"内容重复: {title[:30]}")
            self.redis_client.sadd(DEDUP_HASH_REDIS_SET, dedup_hash)

        return item


class CleanPipeline:
    """数据清洗管道"""

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        # 清洗标题
        title = adapter.get("title", "")
        if title:
            title = re.sub(r"\s+", " ", title).strip()
            adapter["title"] = title

        # 清洗正文
        content = adapter.get("content_raw", "")
        if content:
            # 移除多余空白
            content = re.sub(r"\n{3,}", "\n\n", content)
            content = re.sub(r"[ \t]+", " ", content)
            content = content.strip()
            adapter["content_raw"] = content

        # 解析发布日期
        publish_date = adapter.get("publish_date")
        if publish_date and isinstance(publish_date, str):
            # 尝试多种日期格式
            for fmt in ["%Y-%m-%d", "%Y年%m月%d日", "%Y/%m/%d", "%Y.%m.%d"]:
                try:
                    adapter["publish_date"] = datetime.strptime(publish_date, fmt).date()
                    break
                except ValueError:
                    continue

        # 设置采集时间
        adapter["crawl_time"] = datetime.utcnow()

        return item


class DatabasePipeline:
    """数据库写入管道"""

    def __init__(self):
        self.conn = None
        self.cursor = None

    def open_spider(self, spider):
        # 解析数据库URL
        self.conn = psycopg2.connect(DATABASE_URL)
        self.conn.autocommit = False
        self.cursor = self.conn.cursor()

    def close_spider(self, spider):
        if self.conn:
            self.conn.commit()
            self.cursor.close()
            self.conn.close()

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        try:
            # 插入资讯表（pending_review状态，等待AI处理）
            self.cursor.execute(
                """
                INSERT INTO news_items (
                    title, content_raw, source_type, source_channel,
                    source_url, publish_date, area_tags, industry_tags,
                    dedup_hash, status, created_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending_review', NOW()
                )
                ON CONFLICT (source_url) DO NOTHING
                RETURNING id
                """,
                (
                    adapter.get("title"),
                    adapter.get("content_raw"),
                    adapter.get("source_type"),
                    adapter.get("source_channel"),
                    adapter.get("source_url"),
                    adapter.get("publish_date"),
                    Json(adapter.get("area_scope", [])),
                    Json(adapter.get("industry_scope", [])),
                    adapter.get("dedup_hash"),
                ),
            )

            result = self.cursor.fetchone()
            if result:
                news_id = result[0]
                spider.crawler.stats.inc_value("db/inserted")
                logger.info(f"新增资讯: {adapter.get('title', '')[:30]} (ID: {news_id})")

                # TODO: 触发AI处理任务（通过Celery或消息队列）
                # from app.tasks.ai_tasks import process_news_task
                # process_news_task.delay(str(news_id))
            else:
                spider.crawler.stats.inc_value("db/duplicate")

            self.conn.commit()

        except Exception as e:
            self.conn.rollback()
            logger.error(f"数据库写入失败: {e}")
            spider.crawler.stats.inc_value("db/error")

        return item


class DropItem(Exception):
    """丢弃Item异常"""
    pass
