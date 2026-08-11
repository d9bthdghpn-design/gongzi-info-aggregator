"""
数据模型 - 线索模型
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


class Lead(Base):
    """线索表"""
    __tablename__ = "leads"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_name = Column(String(256), nullable=False, index=True)
    credit_code = Column(String(32))  # 统一社会信用代码
    industry = Column(String(64), index=True)  # 所属行业
    area = Column(String(64), index=True)  # 所在区域
    contact_person = Column(String(64))
    contact_title = Column(String(64))  # 联系人职务
    contact_phone = Column(String(32))
    intent_business = Column(JSON_TYPE, default=list)  # 意向业务
    project_desc = Column(Text)  # 项目描述
    expected_date = Column(Date)  # 预计落地时间
    lead_source = Column(String(32), default="manual")  # 线索来源
    source_news_id = Column(String(36), ForeignKey("news_items.id"))
    priority = Column(Integer, default=3)  # 优先级 1-5
    status = Column(String(32), nullable=False, default="new", index=True)
    # new/active/converted/lost/released
    reporter_id = Column(String(36), ForeignKey("users.id"))
    assignee_id = Column(String(36), ForeignKey("users.id"), index=True)
    public_pool = Column(Boolean, default=False, index=True)  # 是否在公海池
    protect_expire_at = Column(DateTime)  # 保护期到期时间
    last_followup_time = Column(DateTime)
    next_followup_time = Column(DateTime)
    is_deleted = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Lead {self.company_name}>"


class LeadFollowup(Base):
    """线索跟进记录表"""
    __tablename__ = "lead_followups"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lead_id = Column(String(36), ForeignKey("leads.id"), nullable=False, index=True)
    followup_type = Column(String(32), nullable=False)  # phone/visit/email/meeting/other
    content = Column(Text, nullable=False)
    next_action = Column(String(512))
    next_time = Column(DateTime)
    follower_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    followup_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    attachments = Column(JSON_TYPE, default=list)  # 附件列表
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<LeadFollowup {self.lead_id}>"
