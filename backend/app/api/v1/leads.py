"""
线索API - 线索管理、跟进、公海池
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from app.database import get_db
from app.models import User, NewsItem
from app.core.security import get_current_user, require_role
from app.schemas.lead import (
    LeadSchema, LeadCreateSchema, LeadUpdateSchema, LeadQuerySchema,
    LeadFollowupSchema, LeadFollowupCreateSchema, LeadAssignSchema,
    LeadFromNewsSchema, LeadDashboardSchema,
)
from app.schemas.base import PageResponse, DataResponse, ListResponse
from app.services import lead_service, lead_followup_service
from app.core.exceptions import BusinessException

router = APIRouter(prefix="/leads", tags=["线索管理"])


def _can_access_lead(lead, current_user: User) -> bool:
    """判断当前用户是否有权查看/操作该线索：本人、公海池、管理员"""
    if current_user.role == "admin":
        return True
    if lead.public_pool:
        return True
    return str(lead.assignee_id) == str(current_user.id)


def _can_edit_lead(lead, current_user: User) -> bool:
    """判断当前用户是否有权修改该线索：本人或管理员"""
    if current_user.role == "admin":
        return True
    return str(lead.assignee_id) == str(current_user.id)


@router.get("", response_model=PageResponse[List[LeadSchema]])
def get_lead_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None,
    industry: Optional[str] = None,
    area: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[int] = None,
    public_pool: Optional[bool] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取线索列表"""
    query_params = LeadQuerySchema(
        page=page, page_size=page_size, keyword=keyword,
        industry=industry, area=area, status=status,
        priority=priority, public_pool=public_pool,
        sort_by=sort_by, sort_order=sort_order,
    )
    items, total = lead_service.get_lead_list(db, query_params, current_user)
    total_pages = (total + page_size - 1) // page_size

    return PageResponse(
        data=[LeadSchema.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/mine", response_model=PageResponse[List[LeadSchema]])
def get_my_leads(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取我的线索"""
    items, total = lead_service.get_my_leads(db, str(current_user.id), page, page_size)
    total_pages = (total + page_size - 1) // page_size

    return PageResponse(
        data=[LeadSchema.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/public-pool", response_model=PageResponse[List[LeadSchema]])
def get_public_pool_leads(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取公海池线索"""
    items, total = lead_service.get_public_pool_leads(db, page, page_size, keyword)
    total_pages = (total + page_size - 1) // page_size

    return PageResponse(
        data=[LeadSchema.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/dashboard")
def get_lead_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """转化看板：漏斗+分类统计+经理排行"""
    import traceback
    try:
        from sqlalchemy import func, case
        from app.models import Lead, NewsItem

        total_opportunities = db.query(func.count(NewsItem.id)).filter(
            NewsItem.status == "published", NewsItem.is_deleted == False,
        ).scalar() or 0

        base_query = db.query(Lead).filter(Lead.is_deleted == False)
        total_leads = base_query.count()
        active_leads = base_query.filter(Lead.status == "active").count()
        converted_leads = base_query.filter(Lead.status == "converted").count()
        lost_leads = base_query.filter(Lead.status == "lost").count()
        conversion_rate = round(converted_leads / total_leads * 100, 1) if total_leads > 0 else 0.0

        total_estimated = db.query(func.coalesce(func.sum(Lead.estimated_amount), 0)).filter(Lead.is_deleted == False).scalar() or 0
        total_converted = db.query(func.coalesce(func.sum(Lead.converted_amount), 0)).filter(Lead.is_deleted == False).scalar() or 0

        category_rows = db.query(Lead.source_category, func.count(Lead.id), func.coalesce(func.sum(Lead.estimated_amount), 0)).filter(Lead.is_deleted == False, Lead.source_category.isnot(None)).group_by(Lead.source_category).all()
        category_breakdown = [{"category": str(r[0]), "count": int(r[1]), "estimated_amount": float(r[2] or 0)} for r in category_rows]

        manager_rows = db.query(Lead.assignee_id, func.count(Lead.id), func.sum(case((Lead.status == "converted", 1), else_=0)), func.coalesce(func.sum(Lead.converted_amount), 0)).filter(Lead.is_deleted == False, Lead.assignee_id.isnot(None)).group_by(Lead.assignee_id).order_by(func.count(Lead.id).desc()).limit(10).all()
        manager_ranking = []
        for r in manager_rows:
            user = db.query(User).filter(User.id == r[0]).first()
            manager_ranking.append({"manager_name": user.username if user else "未知", "total_leads": int(r[1]), "converted_leads": int(r[2] or 0), "converted_amount": float(r[3] or 0)})

        return {"code": 0, "message": "success", "data": {
            "total_opportunities": int(total_opportunities), "total_leads": int(total_leads),
            "active_leads": int(active_leads), "converted_leads": int(converted_leads),
            "lost_leads": int(lost_leads), "conversion_rate": float(conversion_rate),
            "total_estimated_amount": float(total_estimated or 0), "total_converted_amount": float(total_converted or 0),
            "category_breakdown": category_breakdown, "manager_ranking": manager_ranking,
        }}
    except Exception as e:
        return {"code": 500, "message": f"看板错误: {str(e)[:300]}", "data": {"traceback": traceback.format_exc()[:1000]}}


@router.get("/{lead_id}", response_model=DataResponse[LeadSchema])
def get_lead_detail(
    lead_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取线索详情"""
    lead = lead_service.get(db, lead_id)
    if not lead:
        return DataResponse(code=404, message="线索不存在")
    if not _can_access_lead(lead, current_user):
        raise BusinessException(code=403, message="无权查看该线索")
    return DataResponse(data=LeadSchema.model_validate(lead))


@router.post("", response_model=DataResponse[LeadSchema])
def create_lead(
    obj_in: LeadCreateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建线索"""
    lead = lead_service.create_lead(db, obj_in, str(current_user.id))
    return DataResponse(data=LeadSchema.model_validate(lead))


@router.post("/from-news", response_model=DataResponse[LeadSchema])
def create_lead_from_news(
    obj_in: LeadFromNewsSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """从资讯转线索"""
    news = db.query(NewsItem).filter(NewsItem.id == obj_in.news_id).first()
    if not news:
        raise BusinessException(code=404, message="资讯不存在")

    # 从资讯提取线索信息
    company_name = obj_in.company_name or news.title[:80]
    industry = (news.industry_tags or [None])[0] if news.industry_tags else None
    area = (news.area_tags or [None])[0] if news.area_tags else None

    lead_data = LeadCreateSchema(
        company_name=company_name,
        industry=industry,
        area=area,
        project_desc=f"来源资讯：{news.title}\n{news.content_summary or ''}",
        source_news_id=news.id,
        priority=obj_in.priority,
    )
    lead = lead_service.create_lead(db, lead_data, str(current_user.id))
    lead.lead_source = "news"
    lead.source_category = news.business_category

    # 增加资讯的线索计数
    news.lead_count = (news.lead_count or 0) + 1
    db.commit()
    db.refresh(lead)

    return DataResponse(data=LeadSchema.model_validate(lead))


@router.put("/{lead_id}", response_model=DataResponse[LeadSchema])
def update_lead(
    lead_id: str,
    obj_in: LeadUpdateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新线索"""
    lead = lead_service.get(db, lead_id)
    if not lead:
        return DataResponse(code=404, message="线索不存在")
    if not _can_edit_lead(lead, current_user):
        raise BusinessException(code=403, message="无权修改该线索")

    updated = lead_service.update(db, db_obj=lead, obj_in=obj_in)
    return DataResponse(data=LeadSchema.model_validate(updated))


@router.post("/{lead_id}/claim", response_model=DataResponse[LeadSchema])
def claim_lead(
    lead_id: str,
    protect_days: int = Query(30, description="保护期天数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """领取公海线索"""
    lead = lead_service.claim_lead(db, lead_id, str(current_user.id), protect_days)
    return DataResponse(data=LeadSchema.model_validate(lead))


@router.post("/{lead_id}/release", response_model=DataResponse[LeadSchema])
def release_lead(
    lead_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """释放线索到公海"""
    lead = lead_service.release_lead(db, lead_id, str(current_user.id))
    return DataResponse(data=LeadSchema.model_validate(lead))


@router.post("/{lead_id}/assign", response_model=DataResponse[LeadSchema])
def assign_lead(
    lead_id: str,
    obj_in: LeadAssignSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """分配线索（管理员）"""
    lead = lead_service.assign_lead(db, lead_id, obj_in)
    return DataResponse(data=LeadSchema.model_validate(lead))


# ==================== 转化看板 ====================

# ==================== 跟进记录 ====================

@router.get("/{lead_id}/followups", response_model=PageResponse[List[LeadFollowupSchema]])
def get_lead_followups(
    lead_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取线索跟进记录"""
    lead = lead_service.get(db, lead_id)
    if not lead:
        return DataResponse(code=404, message="线索不存在")
    if not _can_access_lead(lead, current_user):
        raise BusinessException(code=403, message="无权查看该线索的跟进记录")

    items, total = lead_followup_service.get_followups(db, lead_id, page, page_size)
    total_pages = (total + page_size - 1) // page_size

    return PageResponse(
        data=[LeadFollowupSchema.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post("/{lead_id}/followups", response_model=DataResponse[LeadFollowupSchema])
def add_lead_followup(
    lead_id: str,
    obj_in: LeadFollowupCreateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """添加跟进记录"""
    lead = lead_service.get(db, lead_id)
    if not lead:
        return DataResponse(code=404, message="线索不存在")
    if not _can_edit_lead(lead, current_user):
        raise BusinessException(code=403, message="无权跟进该线索")

    followup = lead_followup_service.add_followup(db, lead_id, obj_in, str(current_user.id))
    return DataResponse(data=LeadFollowupSchema.model_validate(followup))
