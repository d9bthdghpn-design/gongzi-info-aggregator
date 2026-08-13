"""
采集任务 - Celery 异步任务
通过 CrawlerRunner 在 Celery worker 进程内执行 Scrapy，无需独立爬虫容器。
"""
import logging
import os
import sys
import json
from datetime import datetime, timezone
from pathlib import Path

from app.tasks.celery_app import celery_app
from app.database import SessionLocal
from app.models import CrawlSource, CrawlLog, NewsItem

logger = logging.getLogger(__name__)

# 将爬虫项目加入 Python 路径
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent  # 项目根目录
_CRAWLER_DIR = _PROJECT_ROOT / "crawler"
if str(_CRAWLER_DIR) not in sys.path:
    sys.path.insert(0, str(_CRAWLER_DIR))

os.environ.setdefault("SCRAPY_SETTINGS_MODULE", "crawler.settings")

# crochet 用于在同步的 Celery 任务中运行 Twisted/Scrapy
try:
    from crochet import setup as crochet_setup, wait_for
    crochet_setup()
    HAS_CROCHET = True
except ImportError:
    HAS_CROCHET = False
    logger.warning("crochet 未安装，采集任务将不可用。请 pip install crochet")


def _get_spider_for_source(source: CrawlSource):
    """根据采集源配置返回 (spider_name, spider_kwargs)"""
    selector_config = source.selector_config or {}
    crawl_type = source.crawl_type or "web"

    # 根据来源类型推导资讯类型
    info_type_map = {"bidding": "bidding", "gov": "policy", "park": "park", "enterprise": "enterprise"}
    info_type = info_type_map.get(source.source_type, "")

    # 基础参数
    kwargs = {
        "source_id": str(source.id),
        "name": source.name,
        "source_type": source.source_type,
        "source_channel": source.name,
        "area_tags": source.area_scope or [],
        "industry_tags": source.industry_scope or [],
        "info_type": info_type,
    }

    if crawl_type == "rss":
        kwargs["feed_url"] = source.entry_url
        return "rss", kwargs
    elif crawl_type == "wechat":
        # 微信公众号：entry_url 存文章URL（逗号分隔），或 selector_config.article_urls
        article_urls = selector_config.get("article_urls", source.entry_url)
        kwargs["article_urls"] = article_urls
        return "wechat", kwargs
    else:
        # web/js 类型都走配置化爬虫 base_config
        kwargs["entry_url"] = source.entry_url
        kwargs["selector_config"] = selector_config
        return "base_config", kwargs


@wait_for(timeout=300)
def _run_spider(spider_name: str, **spider_kwargs):
    """在 Twisted reactor 中运行 Scrapy 爬虫（crochet 同步封装）"""
    from scrapy.crawler import CrawlerRunner
    from scrapy.utils.project import get_project_settings

    runner = CrawlerRunner(get_project_settings())
    return runner.crawl(spider_name, **spider_kwargs)


@celery_app.task(bind=True, name="app.tasks.crawl_tasks.crawl_source")
def crawl_source_task(self, source_id: str):
    """采集单个数据源"""
    logger.info(f"开始采集数据源: {source_id}")

    db = SessionLocal()
    crawl_log = None
    try:
        source = db.query(CrawlSource).filter(CrawlSource.id == source_id).first()
        if not source:
            logger.warning(f"数据源不存在: {source_id}")
            return {"status": "failed", "message": "数据源不存在"}

        # 创建采集日志
        crawl_log = CrawlLog(
            source_id=source.id,
            crawl_start=datetime.now(timezone.utc),
            status="running",
        )
        db.add(crawl_log)
        db.commit()

        # 记录采集前的资讯数
        before_count = db.query(NewsItem).filter(
            NewsItem.source_url.isnot(None)
        ).count()

        # 执行爬虫
        if not HAS_CROCHET:
            raise RuntimeError("crochet 未安装，无法执行采集")

        spider_name, spider_kwargs = _get_spider_for_source(source)
        logger.info(f"执行爬虫 {spider_name}: {source.name}")
        _run_spider(spider_name, **spider_kwargs)

        # 统计结果
        after_count = db.query(NewsItem).count()
        new_count = after_count - before_count

        crawl_log.crawl_end = datetime.now(timezone.utc)
        crawl_log.total_fetched = new_count
        crawl_log.new_count = new_count
        crawl_log.dup_count = 0
        crawl_log.error_count = 0
        crawl_log.status = "success"

        source.last_crawl_at = datetime.now(timezone.utc)
        source.last_crawl_status = "success"
        source.last_error_msg = ""

        db.commit()

        logger.info(f"采集完成: {source.name}, 新增 {new_count} 条")
        return {
            "status": "success",
            "source_id": source_id,
            "source_name": source.name,
            "new_count": new_count,
        }

    except Exception as e:
        logger.exception(f"采集异常: {source_id}, {e}")
        try:
            if crawl_log:
                crawl_log.status = "failed"
                crawl_log.error_msg = str(e)[:500]
                crawl_log.crawl_end = datetime.now(timezone.utc)
            source_obj = db.query(CrawlSource).filter(CrawlSource.id == source_id).first()
            if source_obj:
                source_obj.last_crawl_status = "failed"
                source_obj.last_error_msg = str(e)[:500]
            db.commit()
        except Exception:
            pass
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


@celery_app.task(name="app.tasks.crawl_tasks.crawl_all")
def crawl_all_sources():
    """全量采集所有活跃数据源"""
    logger.info("开始全量采集")

    db = SessionLocal()
    try:
        sources = db.query(CrawlSource).filter(
            CrawlSource.is_active == True
        ).order_by(CrawlSource.priority.desc()).all()

        logger.info(f"待采集数据源数: {len(sources)}")

        results = []
        for source in sources:
            try:
                # 串行执行，避免对政府站造成压力
                result = crawl_source_task.apply_async(args=[str(source.id)])
                results.append({"source_id": str(source.id), "task_id": result.id})
            except Exception as e:
                logger.error(f"提交采集任务失败: {source.name}, {e}")

        return {"total": len(sources), "submitted": len(results), "results": results}
    finally:
        db.close()


@celery_app.task(name="app.tasks.crawl_tasks.crawl_high_priority")
def crawl_high_priority():
    """采集高优先级数据源（招投标等时效性强的）"""
    logger.info("开始高优先级采集")

    db = SessionLocal()
    try:
        sources = db.query(CrawlSource).filter(
            CrawlSource.is_active == True,
            CrawlSource.priority >= 7,
        ).order_by(CrawlSource.priority.desc()).all()

        results = []
        for source in sources:
            try:
                result = crawl_source_task.apply_async(args=[str(source.id)])
                results.append({"source_id": str(source.id), "task_id": result.id})
            except Exception as e:
                logger.error(f"提交采集任务失败: {source.name}, {e}")

        return {"total": len(sources), "submitted": len(results), "results": results}
    finally:
        db.close()
