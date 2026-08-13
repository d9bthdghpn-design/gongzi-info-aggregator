"""
AI处理任务 - Celery异步任务
"""
import logging

from app.tasks.celery_app import celery_app
from app.services import ai_service, RuleEngine
from app.database import SessionLocal
from app.models import NewsItem
from app.config import settings

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="app.tasks.ai_tasks.process_news")
def process_news_task(self, news_id: str):
    """
    处理单条资讯的AI任务
    包括：分类打标、摘要生成、业务启示、质量打分
    高价值资讯即时推送
    """
    logger.info(f"开始AI处理资讯: {news_id}")

    db = SessionLocal()
    try:
        news = db.query(NewsItem).filter(NewsItem.id == news_id).first()
        if not news:
            logger.warning(f"资讯不存在: {news_id}")
            return {"status": "failed", "message": "资讯不存在"}

        # 规则引擎前置过滤
        rule_engine = RuleEngine(db)
        if not rule_engine.should_process_by_ai(news.title, news.content_raw or ""):
            logger.info(f"资讯被规则引擎过滤: {news_id}")
            news.status = "rejected"
            db.commit()
            return {"status": "filtered", "message": "被规则引擎过滤"}

        # AI处理
        success = ai_service.process_news(db, news_id)
        if not success:
            logger.error(f"AI处理失败: {news_id}")
            return {"status": "failed", "news_id": news_id}

        db.refresh(news)
        logger.info(f"AI处理完成: {news_id}, 评分: {news.quality_score}")

        # 根据评分自动发布或待审核
        if news.quality_score and news.quality_score >= settings.AI_AUTO_PUBLISH_SCORE:
            news.status = "published"
            db.commit()

            # 高价值商机即时推送
            if news.quality_score >= settings.HIGH_VALUE_SCORE:
                try:
                    from app.services.push_service import send_message, format_high_value_message
                    text = format_high_value_message(news)
                    send_message(text)
                    logger.info(f"高价值商机已推送: {news_id}")
                except Exception as e:
                    logger.warning(f"高价值推送失败（不影响主流程）: {e}")
        else:
            news.status = "pending_review"
            db.commit()

        return {"status": "success", "news_id": news_id, "score": news.quality_score}

    except Exception as e:
        logger.exception(f"AI处理异常: {news_id}, {e}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


@celery_app.task(name="app.tasks.ai_tasks.process_pending_news")
def process_pending_news(limit: int = 20):
    """批量处理待 AI 处理的资讯"""
    db = SessionLocal()
    try:
        pending = db.query(NewsItem).filter(
            NewsItem.status == "pending_review"
        ).order_by(NewsItem.created_at.asc()).limit(limit).all()

        if not pending:
            return {"status": "success", "processed": 0}

        logger.info(f"待处理资讯: {len(pending)} 条")
        for news in pending:
            process_news_task.delay(str(news.id))

        return {"status": "success", "processed": len(pending)}
    except Exception as e:
        logger.exception(f"批量处理异常: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


@celery_app.task(name="app.tasks.ai_tasks.batch_process_news")
def batch_process_news_task(news_ids: list):
    """批量处理指定资讯"""
    logger.info(f"开始批量AI处理, 数量: {len(news_ids)}")

    results = []
    for news_id in news_ids:
        try:
            result = process_news_task.delay(news_id)
            results.append({"news_id": news_id, "task_id": result.id})
        except Exception as e:
            logger.error(f"提交任务失败: {news_id}, {e}")
            results.append({"news_id": news_id, "error": str(e)})

    return {
        "total": len(news_ids),
        "submitted": len(results),
        "results": results,
    }
