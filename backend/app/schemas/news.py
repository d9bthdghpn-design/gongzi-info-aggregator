"""
Schema - 资讯相关
"""
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field
from app.schemas.base import BaseSchema


class TagSchema(BaseSchema):
    """标签Schema"""
    tag_type: str
    tag_code: str
    tag_name: str
    tag_color: Optional[str] = None
    keywords: List[str] = []
    sort_order: int = 0
    is_active: bool = True


class NewsItemSchema(BaseSchema):
    """资讯Schema（列表用，不含敏感字段）"""
    title: str
    content_summary: Optional[str] = None
    business_category: Optional[str] = None
    area_tags: List[str] = []
    industry_tags: List[str] = []
    info_type: Optional[str] = None
    source_type: Optional[str] = None
    source_channel: Optional[str] = None
    publish_date: Optional[date] = None
    business_tip: Optional[str] = None
    quality_score: int = 0
    score_dimensions: dict = {}  # 7维评分明细
    event_cluster_id: Optional[str] = None  # 事件聚类ID
    status: str = "pending_review"
    view_count: int = 0
    lead_count: int = 0


class NewsItemDetailSchema(NewsItemSchema):
    """资讯详情Schema（含正文，不含source_url）"""
    content_raw: Optional[str] = None


class NewsItemAdminSchema(NewsItemDetailSchema):
    """资讯管理Schema（含敏感字段，仅管理员可见）"""
    source_url: Optional[str] = None
    dedup_hash: Optional[str] = None
    reviewer_id: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_comment: Optional[str] = None


class NewsItemCreateSchema(BaseModel):
    """创建资讯Schema"""
    title: str
    content_raw: Optional[str] = None
    business_category: Optional[str] = None
    area_tags: List[str] = []
    industry_tags: List[str] = []
    info_type: Optional[str] = None
    source_type: Optional[str] = None
    source_channel: Optional[str] = None
    source_url: Optional[str] = None
    publish_date: Optional[date] = None
    business_tip: Optional[str] = None
    quality_score: int = 0
    dedup_hash: Optional[str] = None
    status: str = "pending_review"


class NewsItemUpdateSchema(BaseModel):
    """更新资讯Schema"""
    title: Optional[str] = None
    content_raw: Optional[str] = None
    content_summary: Optional[str] = None
    business_category: Optional[str] = None
    area_tags: Optional[List[str]] = None
    industry_tags: Optional[List[str]] = None
    info_type: Optional[str] = None
    source_type: Optional[str] = None
    source_channel: Optional[str] = None
    publish_date: Optional[date] = None
    business_tip: Optional[str] = None
    quality_score: Optional[int] = None
    status: Optional[str] = None
    review_comment: Optional[str] = None


class NewsQuerySchema(BaseModel):
    """资讯查询参数"""
    page: int = 1
    page_size: int = 20
    keyword: Optional[str] = None
    business_category: Optional[str] = None
    area_tags: Optional[List[str]] = None
    industry_tags: Optional[List[str]] = None
    info_type: Optional[str] = None
    status: Optional[str] = "published"
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    min_quality_score: Optional[int] = None
    sort_by: str = "publish_date"
    sort_order: str = "desc"


class NewsStatsSchema(BaseModel):
    """资讯统计Schema"""
    today_new: int = 0
    bidding_count: int = 0
    policy_count: int = 0
    enterprise_count: int = 0
    high_value_count: int = 0
    today_new_trend: float = 0.0  # 环比变化率
    last_updated: Optional[str] = None  # 最后更新时间


class TopicSchema(BaseSchema):
    """专题Schema"""
    title: str
    description: Optional[str] = None
    cover_image: Optional[str] = None
    filter_config: dict = {}
    sort_order: int = 0
    is_active: bool = True
    total_count: Optional[int] = None  # 专题下资讯总数
    month_new_count: Optional[int] = None  # 本月新增
    high_value_count: Optional[int] = None  # 高价值数量


class EventClusterSchema(BaseSchema):
    """事件聚类Schema"""
    title: str
    description: Optional[str] = None
    event_type: Optional[str] = None
    news_count: int = 0
    news_ids: List[str] = []
    source_channels: List[str] = []
    first_publish_date: Optional[date] = None
    last_publish_date: Optional[date] = None
    max_quality_score: int = 0


class EventClusterDetailSchema(EventClusterSchema):
    """事件聚类详情Schema（含关联资讯列表）"""
    news_items: List[NewsItemSchema] = []
