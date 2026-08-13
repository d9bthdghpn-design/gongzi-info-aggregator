"""
线索定时任务 - 保护期回收等
"""
import logging
from datetime import datetime, timezone

from app.tasks.celery_app import celery_app
from app.database import SessionLocal
from app.models import Lead

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.lead_tasks.expire_lead_protection")
def expire_lead_protection():
    """
    将保护期到期的线索回收至公海池。
    条件：非公开、有保护期到期时间、已到期、状态为 active/new
    """
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        expired_leads = db.query(Lead).filter(
            Lead.public_pool == False,
            Lead.protect_expire_at.isnot(None),
            Lead.protect_expire_at < now,
            Lead.status.in_(["new", "active"]),
            Lead.is_deleted == False,
        ).all()

        count = 0
        for lead in expired_leads:
            lead.public_pool = True
            lead.assignee_id = None
            lead.status = "released"
            count += 1

        db.commit()
        logger.info(f"保护期回收完成，共回收 {count} 条线索至公海")
        return {"released": count}
    except Exception as e:
        logger.exception(f"保护期回收失败: {e}")
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()
