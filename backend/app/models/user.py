"""
数据模型 - 用户模型
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.sql import func

from app.database import Base


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(64), unique=True, nullable=False, index=True)
    email = Column(String(128))
    phone = Column(String(20))
    full_name = Column(String(64))
    avatar_url = Column(String(512))
    department = Column(String(128))
    position = Column(String(64))
    role = Column(String(32), nullable=False, default="viewer", index=True)  # admin/editor/reviewer/viewer
    password_hash = Column(String(256), nullable=False, default="")
    sso_provider = Column(String(32))  # wecom/feishu
    sso_openid = Column(String(128))
    is_active = Column(Boolean, default=True)
    last_login_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<User {self.username}>"
