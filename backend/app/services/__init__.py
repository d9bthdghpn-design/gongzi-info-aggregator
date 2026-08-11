"""
服务层统一导出
"""
from app.services.news_service import news_service, tag_service, topic_service
from app.services.lead_service import lead_service, lead_followup_service
from app.services.user_service import user_service
from app.services.briefing_service import briefing_service
from app.services.ai_service import ai_service, RuleEngine

__all__ = [
    "news_service", "tag_service", "topic_service",
    "lead_service", "lead_followup_service",
    "user_service", "briefing_service",
    "ai_service", "RuleEngine",
]
