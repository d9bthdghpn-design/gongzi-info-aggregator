"""
Schema - 线索相关
"""
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field
from app.schemas.base import BaseSchema


class LeadSchema(BaseSchema):
    """线索Schema"""
    company_name: str
    credit_code: Optional[str] = None
    industry: Optional[str] = None
    area: Optional[str] = None
    contact_person: Optional[str] = None
    contact_title: Optional[str] = None
    contact_phone: Optional[str] = None  # 按权限脱敏
    intent_business: List[str] = []
    project_desc: Optional[str] = None
    expected_date: Optional[date] = None
    lead_source: str = "manual"
    source_news_id: Optional[str] = None
    source_category: Optional[str] = None
    estimated_amount: Optional[float] = None
    converted_amount: Optional[float] = None
    priority: int = 3
    status: str = "new"
    reporter_id: Optional[str] = None
    assignee_id: Optional[str] = None
    public_pool: bool = False
    protect_expire_at: Optional[datetime] = None
    last_followup_time: Optional[datetime] = None
    next_followup_time: Optional[datetime] = None


class LeadCreateSchema(BaseModel):
    """创建线索Schema"""
    company_name: str
    credit_code: Optional[str] = None
    industry: Optional[str] = None
    area: Optional[str] = None
    contact_person: Optional[str] = None
    contact_title: Optional[str] = None
    contact_phone: Optional[str] = None
    intent_business: List[str] = []
    project_desc: Optional[str] = None
    expected_date: Optional[date] = None
    source_news_id: Optional[str] = None
    priority: int = 3


class LeadUpdateSchema(BaseModel):
    """更新线索Schema"""
    company_name: Optional[str] = None
    credit_code: Optional[str] = None
    industry: Optional[str] = None
    area: Optional[str] = None
    contact_person: Optional[str] = None
    contact_title: Optional[str] = None
    contact_phone: Optional[str] = None
    intent_business: Optional[List[str]] = None
    project_desc: Optional[str] = None
    expected_date: Optional[date] = None
    source_category: Optional[str] = None
    estimated_amount: Optional[float] = None
    converted_amount: Optional[float] = None
    priority: Optional[int] = None
    status: Optional[str] = None


class LeadFollowupSchema(BaseSchema):
    """线索跟进记录Schema"""
    lead_id: str
    followup_type: str
    content: str
    next_action: Optional[str] = None
    next_time: Optional[datetime] = None
    follower_id: Optional[str] = None
    followup_time: Optional[datetime] = None
    attachments: List[dict] = []


class LeadFollowupCreateSchema(BaseModel):
    """创建跟进记录Schema"""
    followup_type: str
    content: str
    next_action: Optional[str] = None
    next_time: Optional[datetime] = None
    attachments: List[dict] = []


class LeadQuerySchema(BaseModel):
    """线索查询参数"""
    page: int = 1
    page_size: int = 20
    keyword: Optional[str] = None
    industry: Optional[str] = None
    area: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[int] = None
    public_pool: Optional[bool] = None
    assignee_id: Optional[str] = None
    sort_by: str = "created_at"
    sort_order: str = "desc"


class LeadAssignSchema(BaseModel):
    """线索分配Schema"""
    assignee_id: str
    protect_days: int = 30  # 保护期天数


class LeadFromNewsSchema(BaseModel):
    """从资讯转线索Schema"""
    news_id: str
    company_name: Optional[str] = None  # 可选，不传则用资讯标题
    priority: int = 3


class LeadDashboardSchema(BaseModel):
    """转化看板Schema"""
    total_opportunities: int = 0  # 系统商机数（已发布资讯）
    total_leads: int = 0  # 转线索数
    active_leads: int = 0  # 跟进中
    converted_leads: int = 0  # 已转化
    lost_leads: int = 0  # 已流失
    conversion_rate: float = 0.0  # 转化率
    total_estimated_amount: float = 0.0  # 预估总金额
    total_converted_amount: float = 0.0  # 实际转化总金额
    category_breakdown: List[dict] = []  # 按行动分类统计
    manager_ranking: List[dict] = []  # 经理排行
