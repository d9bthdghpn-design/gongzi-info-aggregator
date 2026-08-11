"""
Celery应用配置
"""
from celery import Celery
from app.config import settings

celery_app = Celery(
    "gongzi_tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.ai_tasks",
        "app.tasks.crawl_tasks",
        "app.tasks.briefing_tasks",
    ],
)

# 配置
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30分钟超时
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# 定时任务
celery_app.conf.beat_schedule = {
    # 每日凌晨2点全量采集
    "daily-full-crawl": {
        "task": "app.tasks.crawl_tasks.full_crawl",
        "schedule": 3600 * 24,  # 每24小时
        "args": (),
    },
    # 每日中午12点增量采集
    "noon-incremental-crawl": {
        "task": "app.tasks.crawl_tasks.incremental_crawl",
        "schedule": 3600 * 12,  # 每12小时
        "args": (),
    },
    # 每日7:30生成简报
    "daily-briefing-generate": {
        "task": "app.tasks.briefing_tasks.generate_daily_briefing",
        "schedule": 3600 * 24,  # 每24小时
        "args": (),
    },
    # 每小时重点渠道轮询
    "hourly-high-priority-crawl": {
        "task": "app.tasks.crawl_tasks.high_priority_crawl",
        "schedule": 3600,  # 每小时
        "args": (),
    },
}


if __name__ == "__main__":
    celery_app.start()
