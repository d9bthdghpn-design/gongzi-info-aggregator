"""
线索API - 线索管理、跟进、公海池
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from app.database import get_db
from app.models import User
from app.core.security import get_current_user, require_role
from app.schemas.lead import (
    LeadSchema, LeadCreateSchema, LeadUpdateSchema, LeadQuerySchema,
    LeadFollowupSchema, LeadFollowupCreateSchema, LeadAssignSchema,
)
from app.schemas.base import PageResponse, DataResponse, ListResponse
from app.services import lead_service, lead_followup_service

router = APIRouter(prefix="/leads", tags=["线索管理"])


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
    followup = lead_followup_service.add_followup(db, lead_id, obj_in, str(current_user.id))
    return DataResponse(data=LeadFollowupSchema.model_validate(followup))
