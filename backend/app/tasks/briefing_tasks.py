"""
简报任务 - Celery定时任务
"""
import logging
from datetime import date

from app.tasks.celery_app import celery_app
from app.database import SessionLocal
from app.services import briefing_service
from app.services.push_service import send_message, format_briefing_message

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.briefing_tasks.generate_daily_briefing")
def generate_daily_briefing():
    """生成每日简报（定时任务）"""
    logger.info("开始生成每日简报")

    db = SessionLocal()
    try:
        today = date.today()

        existing = briefing_service.get_briefing_by_date(db, today)
        if existing:
            logger.info(f"今日简报已存在: {today}")
            return {"status": "exists", "date": str(today)}

        briefing = briefing_service.generate_briefing(db, today)

        logger.info(f"每日简报生成完成: {today}, 共{briefing.total_count}条资讯")
        return {
            "status": "success",
            "date": str(today),
            "total_count": briefing.total_count,
            "briefing_id": str(briefing.id),
        }

    except Exception as e:
        logger.exception(f"生成每日简报异常: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


@celery_app.task(name="app.tasks.briefing_tasks.push_daily_briefing")
def push_daily_briefing():
    """推送每日简报到飞书/企微（定时任务）"""
    logger.info("开始推送每日简报")

    db = SessionLocal()
    try:
        today = date.today()
        briefing = briefing_service.get_briefing_by_date(db, today)

        if not briefing:
            # 如果简报还没生成，先生成
            logger.info(f"今日简报不存在，先生成: {today}")
            briefing = briefing_service.generate_briefing(db, today)

        if briefing.is_pushed:
            logger.info(f"今日简报已推送: {today}")
            return {"status": "exists", "date": str(today)}

        if briefing.total_count == 0:
            logger.info(f"今日无资讯，跳过推送: {today}")
            return {"status": "skipped", "reason": "无资讯"}

        # 格式化并推送
        text = format_briefing_message(briefing)
        results = send_message(text)

        if any(results.values()):
            briefing_service.push_briefing(db, str(briefing.id))
            logger.info(f"每日简报推送完成: {today}, 结果: {results}")
            return {"status": "success", "date": str(today), "channels": results}
        else:
            logger.warning(f"每日简报推送失败: {today}, 结果: {results}")
            return {"status": "failed", "channels": results}

    except Exception as e:
        logger.exception(f"推送每日简报异常: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()
