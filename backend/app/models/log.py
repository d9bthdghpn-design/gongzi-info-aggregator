"""
数据模型 - 简报与日志模型
"""
import uuid
from datetime import datetime, date

from sqlalchemy import Column, String, Boolean, DateTime, Date, Integer, Text, ForeignKey
from sqlalchemy.sql import func

from app.database import Base

# 兼容SQLite的JSON字段
try:
    from sqlalchemy.dialects.postgresql import JSON
    JSON_TYPE = JSON
except ImportError:
    from sqlalchemy import JSON
    JSON_TYPE = JSON


class DailyBriefing(Base):
    """每日简报表"""
    __tablename__ = "daily_briefings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    brief_date = Column(Date, unique=True, nullable=False, index=True)
    area_scope = Column(String(64))
    content_json = Column(JSON_TYPE, default=dict, nullable=False)
    total_count = Column(Integer, default=0)
    category_counts = Column(JSON_TYPE, default=dict)
    is_pushed = Column(Boolean, default=False, index=True)
    pushed_at = Column(DateTime)
    created_by = Column(String(36), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<DailyBriefing {self.brief_date}>"


class CrawlLog(Base):
    """采集日志表"""
    __tablename__ = "crawl_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_id = Column(String(36), ForeignKey("crawl_sources.id"), nullable=False, index=True)
    crawl_start = Column(DateTime, nullable=False)
    crawl_end = Column(DateTime)
    total_fetched = Column(Integer, default=0)
    new_count = Column(Integer, default=0)
    dup_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    error_msg = Column(Text)
    status = Column(String(16), default="running", index=True)  # running/success/failed
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<CrawlLog {self.source_id}>"


class AIProcessLog(Base):
    """AI处理日志表"""
    __tablename__ = "ai_process_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    news_id = Column(String(36), ForeignKey("news_items.id"), nullable=False, index=True)
    process_type = Column(String(32), nullable=False, index=True)  # classify/summarize/tip/score/all
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    model_version = Column(String(64))
    raw_output = Column(Text)
    is_modified = Column(Boolean, default=False)
    modified_fields = Column(JSON_TYPE, default=list)
    duration_ms = Column(Integer, default=0)
    success = Column(Boolean, default=True, index=True)
    error_msg = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<AIProcessLog {self.news_id}>"


class OperationLog(Base):
    """操作日志表"""
    __tablename__ = "operation_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), index=True)
    action = Column(String(64), nullable=False, index=True)  # create/update/delete/audit/assign
    target_type = Column(String(32), nullable=False)  # news/lead/user/source
    target_id = Column(String(36), nullable=False)
    old_value = Column(JSON_TYPE)
    new_value = Column(JSON_TYPE)
    ip_address = Column(String(64))
    user_agent = Column(String(512))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<OperationLog {self.action}:{self.target_type}>"
