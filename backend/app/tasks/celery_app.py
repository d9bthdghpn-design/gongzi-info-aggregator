"""
Celery应用配置
"""
from celery import Celery
from celery.schedules import crontab
from app.config import settings

celery_app = Celery(
    "gongzi_tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.ai_tasks",
        "app.tasks.crawl_tasks",
        "app.tasks.briefing_tasks",
        "app.tasks.lead_tasks",
    ],
)

# 配置
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=False,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30分钟超时
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# 定时任务（北京时间）
celery_app.conf.beat_schedule = {
    # 每天 06:00 全量采集
    "daily-full-crawl": {
        "task": "app.tasks.crawl_tasks.crawl_all",
        "schedule": crontab(hour=6, minute=0),
    },
    # 每小时采集高优先级源（招投标等时效性强的）
    "hourly-high-priority-crawl": {
        "task": "app.tasks.crawl_tasks.crawl_high_priority",
        "schedule": crontab(minute=0),  # 每整点
    },
    # 每 5 分钟处理待 AI 处理的资讯
    "process-pending-news": {
        "task": "app.tasks.ai_tasks.process_pending_news",
        "schedule": crontab(minute="*/5"),
    },
    # 每天 07:00 生成简报
    "daily-briefing-generate": {
        "task": "app.tasks.briefing_tasks.generate_daily_briefing",
        "schedule": crontab(hour=7, minute=0),
    },
    # 每天 07:30 推送简报
    "daily-briefing-push": {
        "task": "app.tasks.briefing_tasks.push_daily_briefing",
        "schedule": crontab(
            hour=settings.BRIEFING_PUSH_HOUR,
            minute=settings.BRIEFING_PUSH_MINUTE,
        ),
    },
    # 每天凌晨 1:00 回收过期保护期线索到公海
    "expire-lead-protection": {
        "task": "app.tasks.lead_tasks.expire_lead_protection",
        "schedule": crontab(hour=1, minute=0),
    },
}


if __name__ == "__main__":
    celery_app.start()
