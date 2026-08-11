"""
简报任务 - Celery定时任务
"""
import logging
logger = logging.getLogger(__name__)
from datetime import date
from app.tasks.celery_app import celery_app
from app.database import SessionLocal
from app.services import briefing_service


@celery_app.task(name="app.tasks.briefing_tasks.generate_daily_briefing")
def generate_daily_briefing():
    """生成每日简报（定时任务）"""
    logger.info("开始生成每日简报")

    db = SessionLocal()
    try:
        today = date.today()

        # 检查是否已生成
        existing = briefing_service.get_briefing_by_date(db, today)
        if existing:
            logger.info(f"今日简报已存在: {today}")
            return {"status": "exists", "date": str(today)}

        # 生成简报
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
    """推送每日简报（定时任务）"""
    logger.info("开始推送每日简报")

    db = SessionLocal()
    try:
        today = date.today()
        briefing = briefing_service.get_briefing_by_date(db, today)

        if not briefing:
            logger.warning(f"今日简报不存在: {today}")
            return {"status": "failed", "message": "今日简报不存在"}

        if briefing.is_pushed:
            logger.info(f"今日简报已推送: {today}")
            return {"status": "exists", "date": str(today)}

        # TODO: 实际推送逻辑（企业微信/飞书机器人等）
        logger.info(f"推送简报到企业微信/飞书: {today}")

        # 标记为已推送
        briefing_service.push_briefing(db, str(briefing.id))

        logger.info(f"每日简报推送完成: {today}")
        return {
            "status": "success",
            "date": str(today),
            "total_count": briefing.total_count,
        }

    except Exception as e:
        logger.exception(f"推送每日简报异常: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


@celery_app.task(name="app.tasks.briefing_tasks.expire_lead_protection")
def expire_lead_protection():
    """线索保护期到期自动回收（定时任务）"""
    logger.info("开始检查线索保护期到期")

    db = SessionLocal()
    try:
        from datetime import datetime
        from app.models import Lead

        # 查找保护期已到期且在个人池中的线索
        expired_leads = db.query(Lead).filter(
            Lead.public_pool == False,
            Lead.protect_expire_at.isnot(None),
            Lead.protect_expire_at < datetime.utcnow(),
            Lead.status == "active",
        ).all()

        count = 0
        for lead in expired_leads:
            lead.public_pool = True
            lead.assignee_id = None
            lead.status = "released"
            count += 1

        db.commit()
        logger.info(f"线索保护期到期回收完成: {count}条")
        return {"status": "success", "expired_count": count}

    except Exception as e:
        logger.exception(f"线索保护期回收异常: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()
