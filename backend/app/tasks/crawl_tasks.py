"""
采集任务 - Celery异步任务
"""
import logging
logger = logging.getLogger(__name__)
from datetime import datetime
from app.tasks.celery_app import celery_app
from app.database import SessionLocal
from app.models import CrawlSource, CrawlLog
from app.tasks.ai_tasks import process_news_task


@celery_app.task(name="app.tasks.crawl_tasks.full_crawl")
def full_crawl():
    """全量采集（所有活跃渠道）"""
    logger.info("开始全量采集")

    db = SessionLocal()
    try:
        sources = db.query(CrawlSource).filter(
            CrawlSource.is_active == True
        ).order_by(CrawlSource.priority.desc()).all()

        logger.info(f"待采集渠道数: {len(sources)}")

        results = []
        for source in sources:
            try:
                result = crawl_source_task.delay(str(source.id))
                results.append({"source_id": str(source.id), "task_id": result.id})
            except Exception as e:
                logger.error(f"提交采集任务失败: {source.name}, {e}")

        return {
            "total": len(sources),
            "submitted": len(results),
            "results": results,
        }
    finally:
        db.close()


@celery_app.task(name="app.tasks.crawl_tasks.incremental_crawl")
def incremental_crawl():
    """增量采集（高优先级渠道）"""
    logger.info("开始增量采集（高优先级）")

    db = SessionLocal()
    try:
        sources = db.query(CrawlSource).filter(
            CrawlSource.is_active == True,
            CrawlSource.priority >= 7,  # 优先级>=7的高优先级渠道
        ).order_by(CrawlSource.priority.desc()).all()

        logger.info(f"待采集渠道数: {len(sources)}")

        results = []
        for source in sources:
            try:
                result = crawl_source_task.delay(str(source.id))
                results.append({"source_id": str(source.id), "task_id": result.id})
            except Exception as e:
                logger.error(f"提交采集任务失败: {source.name}, {e}")

        return {
            "total": len(sources),
            "submitted": len(results),
            "results": results,
        }
    finally:
        db.close()


@celery_app.task(name="app.tasks.crawl_tasks.high_priority_crawl")
def high_priority_crawl():
    """重点渠道轮询（时效性强的，如招投标）"""
    logger.info("开始重点渠道轮询")

    db = SessionLocal()
    try:
        sources = db.query(CrawlSource).filter(
            CrawlSource.is_active == True,
            CrawlSource.source_type == "bidding",  # 招投标等时效性强的
        ).all()

        logger.info(f"待采集渠道数: {len(sources)}")

        results = []
        for source in sources:
            try:
                result = crawl_source_task.delay(str(source.id))
                results.append({"source_id": str(source.id), "task_id": result.id})
            except Exception as e:
                logger.error(f"提交采集任务失败: {source.name}, {e}")

        return {
            "total": len(sources),
            "submitted": len(results),
            "results": results,
        }
    finally:
        db.close()


@celery_app.task(bind=True, name="app.tasks.crawl_tasks.crawl_source")
def crawl_source_task(self, source_id: str):
    """
    采集单个渠道
    实际采集由Scrapy服务执行，这里通过API或消息队列触发
    """
    logger.info(f"开始采集渠道: {source_id}")

    db = SessionLocal()
    try:
        source = db.query(CrawlSource).filter(CrawlSource.id == source_id).first()
        if not source:
            logger.warning(f"渠道不存在: {source_id}")
            return {"status": "failed", "message": "渠道不存在"}

        # 创建采集日志
        crawl_log = CrawlLog(
            source_id=source.id,
            crawl_start=datetime.utcnow(),
            status="running",
        )
        db.add(crawl_log)
        db.commit()

        # TODO: 实际调用Scrapy采集服务
        # 这里是占位，实际应通过Scrapyd API或消息队列触发Scrapy爬虫
        logger.info(f"触发Scrapy采集: {source.name}")

        # 模拟采集完成（实际应由Scrapy回调更新）
        crawl_log.crawl_end = datetime.utcnow()
        crawl_log.total_fetched = 0
        crawl_log.new_count = 0
        crawl_log.dup_count = 0
        crawl_log.error_count = 0
        crawl_log.status = "success"

        source.last_crawl_at = datetime.utcnow()
        source.last_crawl_status = "success"

        db.commit()

        # 采集完成后，触发AI处理（新采集的资讯）
        # TODO: 获取新采集的资讯ID列表，批量提交AI处理

        logger.info(f"采集完成: {source.name}")
        return {
            "status": "success",
            "source_id": source_id,
            "source_name": source.name,
            "total_fetched": crawl_log.total_fetched,
            "new_count": crawl_log.new_count,
        }

    except Exception as e:
        logger.exception(f"采集异常: {source_id}, {e}")

        # 更新失败状态
        try:
            crawl_log = db.query(CrawlLog).filter(
                CrawlLog.source_id == source_id
            ).order_by(CrawlLog.crawl_start.desc()).first()
            if crawl_log:
                crawl_log.status = "failed"
                crawl_log.error_msg = str(e)
                crawl_log.crawl_end = datetime.utcnow()

            source = db.query(CrawlSource).filter(CrawlSource.id == source_id).first()
            if source:
                source.last_crawl_status = "failed"
                source.last_error_msg = str(e)

            db.commit()
        except Exception:
            pass

        return {"status": "error", "message": str(e)}
    finally:
        db.close()
