"""
Scrapy管道 - 去重、清洗、入库
"""
import hashlib
import re
from datetime import datetime, timezone
from loguru import logger

try:
    import redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False

from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem

from crawler.settings import REDIS_URL, DATABASE_URL, DEDUP_REDIS_SET, DEDUP_HASH_REDIS_SET


class DedupPipeline:
    """去重管道（L1 URL去重 + L2 内容去重），Redis 不可用时降级为内存去重"""

    def __init__(self):
        self.redis_client = None
        self._mem_urls = set()
        self._mem_hashes = set()

    def open_spider(self, spider):
        if HAS_REDIS:
            try:
                self.redis_client = redis.from_url(REDIS_URL, socket_connect_timeout=3)
                self.redis_client.ping()
            except Exception as e:
                logger.warning(f"Redis 不可用，降级为内存去重: {e}")
                self.redis_client = None

    def _seen_url(self, url: str) -> bool:
        if self.redis_client:
            if self.redis_client.sismember(DEDUP_REDIS_SET, url):
                return True
            self.redis_client.sadd(DEDUP_REDIS_SET, url)
            return False
        if url in self._mem_urls:
            return True
        self._mem_urls.add(url)
        return False

    def _seen_hash(self, h: str) -> bool:
        if self.redis_client:
            if self.redis_client.sismember(DEDUP_HASH_REDIS_SET, h):
                return True
            self.redis_client.sadd(DEDUP_HASH_REDIS_SET, h)
            return False
        if h in self._mem_hashes:
            return True
        self._mem_hashes.add(h)
        return False

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        source_url = adapter.get("source_url")
        title = adapter.get("title", "")
        content = adapter.get("content_raw", "")

        # L1: URL去重
        if source_url and self._seen_url(source_url):
            spider.crawler.stats.inc_value("dedup/url_duplicate")
            raise DropItem(f"URL重复: {source_url}")

        # L2: 内容去重（标题+正文前500字MD5）
        if title and content:
            dedup_text = title + (content[:500] if content else "")
            dedup_hash = hashlib.md5(dedup_text.encode("utf-8")).hexdigest()
            adapter["dedup_hash"] = dedup_hash

            if self._seen_hash(dedup_hash):
                spider.crawler.stats.inc_value("dedup/content_duplicate")
                raise DropItem(f"内容重复: {title[:30]}")

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
            content = re.sub(r"\n{3,}", "\n\n", content)
            content = re.sub(r"[ \t]+", " ", content)
            content = content.strip()
            adapter["content_raw"] = content

        # 解析发布日期
        publish_date = adapter.get("publish_date")
        if publish_date and isinstance(publish_date, str):
            date_str = publish_date.strip()
            # 正则提取纯日期部分（去掉"发布时间："等前缀）
            m = re.search(r"\d{4}[-/年.]\d{1,2}[-/月.]\d{1,2}(?:日)?(?:\s+\d{1,2}:\d{2}(?::\d{2})?)?", date_str)
            if m:
                date_str = m.group(0)
            for fmt in [
                "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M",
                "%Y-%m-%d", "%Y年%m月%d日", "%Y/%m/%d", "%Y.%m.%d",
            ]:
                try:
                    adapter["publish_date"] = datetime.strptime(date_str, fmt).date()
                    break
                except ValueError:
                    continue

        adapter["crawl_time"] = datetime.now(timezone.utc)
        return item


class DatabasePipeline:
    """数据库写入管道（SQLAlchemy ORM，与后端模型统一）"""

    def __init__(self):
        self.session_factory = None

    def open_spider(self, spider):
        try:
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            engine = create_engine(DATABASE_URL, pool_pre_ping=True)
            self.session_factory = sessionmaker(bind=engine)
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            raise

    def close_spider(self, spider):
        pass

    def process_item(self, item, spider):
        from app.models import NewsItem

        adapter = ItemAdapter(item)
        session = self.session_factory()
        try:
            # 检查 source_url 是否已存在
            source_url = adapter.get("source_url")
            exists = session.query(NewsItem).filter(
                NewsItem.source_url == source_url
            ).first() if source_url else None

            if exists:
                spider.crawler.stats.inc_value("db/duplicate")
                return item

            news = NewsItem(
                title=adapter.get("title"),
                content_raw=adapter.get("content_raw"),
                source_type=adapter.get("source_type", "gov"),
                source_channel=adapter.get("source_channel", ""),
                source_url=source_url,
                publish_date=adapter.get("publish_date"),
                area_tags=adapter.get("area_tags", []),
                industry_tags=adapter.get("industry_tags", []),
                info_type=adapter.get("info_type", ""),
                dedup_hash=adapter.get("dedup_hash"),
                status="pending_review",
            )
            session.add(news)
            session.commit()
            session.refresh(news)
            spider.crawler.stats.inc_value("db/inserted")
            logger.info(f"新增资讯: {adapter.get('title', '')[:40]} (ID: {news.id})")

            # 触发 AI 处理任务
            try:
                from app.tasks.ai_tasks import process_news_task
                process_news_task.delay(str(news.id))
            except Exception as e:
                logger.warning(f"AI 任务派发失败（不影响入库）: {e}")

        except Exception as e:
            session.rollback()
            logger.error(f"数据库写入失败: {e}")
            spider.crawler.stats.inc_value("db/error")
        finally:
            session.close()

        return item
