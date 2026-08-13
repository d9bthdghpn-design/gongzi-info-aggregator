"""
数据模型 - 资讯模型
"""
import uuid
import json
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


class NewsItem(Base):
    """资讯主表"""
    __tablename__ = "news_items"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(512), nullable=False)
    content_raw = Column(Text)
    content_summary = Column(String(500))
    business_category = Column(String(64), index=True)  # 业务分类标签code
    area_tags = Column(JSON_TYPE, default=list)  # 区域标签数组
    industry_tags = Column(JSON_TYPE, default=list)  # 行业标签数组
    info_type = Column(String(32), index=True)  # 资讯类型: policy/bidding/enterprise/park
    source_type = Column(String(32))  # 来源类型
    source_channel = Column(String(128))  # 来源渠道名称
    source_url = Column(String(1024), unique=True)  # 原始URL(仅后台)
    publish_date = Column(Date, index=True)  # 发布日期
    business_tip = Column(Text)  # AI生成的业务启示
    quality_score = Column(Integer, default=0)  # 商机价值评分 0-100（7维加权总分）
    score_dimensions = Column(JSON_TYPE, default=dict)  # 7维评分明细: {event_severity, impact_scope, asset_sensitivity, credibility, novelty, timeliness, confidence}
    event_cluster_id = Column(String(36), index=True)  # 事件聚类ID（关联event_clusters表）
    dedup_hash = Column(String(64), unique=True)  # 内容去重哈希
    status = Column(String(32), nullable=False, default="pending_review", index=True)
    # pending_review/published/rejected/ai_failed
    reviewer_id = Column(String(36), ForeignKey("users.id"))
    reviewed_at = Column(DateTime)
    review_comment = Column(String(512))
    view_count = Column(Integer, default=0)
    lead_count = Column(Integer, default=0)
    is_deleted = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<NewsItem {self.title[:30]}>"


class TagDictionary(Base):
    """标签字典表"""
    __tablename__ = "tag_dictionary"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tag_type = Column(String(32), nullable=False, index=True)  # business/area/industry/info_type
    tag_code = Column(String(64), nullable=False)
    tag_name = Column(String(64), nullable=False)
    tag_color = Column(String(16))
    keywords = Column(JSON_TYPE, default=list)  # 关键词列表
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Tag {self.tag_type}:{self.tag_name}>"


class CrawlSource(Base):
    """采集渠道配置表"""
    __tablename__ = "crawl_sources"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(128), nullable=False)
    source_type = Column(String(32), nullable=False)  # gov/park/enterprise/bidding/wechat/xhs
    crawl_type = Column(String(32), nullable=False)  # web/js/rss/wechat/xhs
    entry_url = Column(String(512), nullable=False)
    area_scope = Column(JSON_TYPE, default=list)  # 区域范围标签
    industry_scope = Column(JSON_TYPE, default=list)  # 行业范围标签
    crawl_interval_hours = Column(Integer, default=24)
    priority = Column(Integer, default=5, index=True)  # 1-10
    is_active = Column(Boolean, default=True, index=True)
    selector_config = Column(JSON_TYPE, default=dict)  # 解析规则配置
    headers = Column(JSON_TYPE, default=dict)  # 请求头配置
    proxy_group = Column(String(32))  # 代理池分组
    last_crawl_at = Column(DateTime)
    last_crawl_status = Column(String(16))
    last_error_msg = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<CrawlSource {self.name}>"


class Topic(Base):
    """业务专题表"""
    __tablename__ = "topics"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(256), nullable=False)
    description = Column(Text)
    cover_image = Column(String(512))
    filter_config = Column(JSON_TYPE, default=dict)  # 筛选条件配置
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True, index=True)
    created_by = Column(String(36), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Topic {self.title}>"


class EventCluster(Base):
    """事件聚类表 - 同一政策/事件多源发布自动聚合"""
    __tablename__ = "event_clusters"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(512), nullable=False)  # 事件标题（取最早/最高质量资讯标题）
    description = Column(Text)  # 事件描述
    event_type = Column(String(32), index=True)  # 事件类型: policy/regulation/announcement/other
    news_count = Column(Integer, default=0)  # 关联资讯数量
    news_ids = Column(JSON_TYPE, default=list)  # 关联资讯ID列表
    source_channels = Column(JSON_TYPE, default=list)  # 涉及的来源渠道列表
    first_publish_date = Column(Date, index=True)  # 最早发布日期
    last_publish_date = Column(Date)  # 最晚发布日期
    max_quality_score = Column(Integer, default=0)  # 最高质量分
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<EventCluster {self.title[:30]}>"
