"""
资讯API - 资讯列表、详情、统计
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date

from app.database import get_db
from app.models import User
from app.core.security import get_current_user, require_role
from app.schemas.news import (
    NewsItemSchema, NewsItemDetailSchema, NewsItemAdminSchema,
    NewsItemUpdateSchema, NewsQuerySchema, NewsStatsSchema,
    TagSchema, TopicSchema,
)
from app.schemas.base import PageResponse, DataResponse, ListResponse
from app.services import news_service, tag_service, topic_service

router = APIRouter(prefix="/news", tags=["资讯管理"])


@router.get("/stats", response_model=DataResponse[NewsStatsSchema])
def get_news_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取资讯统计数据"""
    stats = news_service.get_stats(db)
    return DataResponse(data=stats)


@router.get("", response_model=PageResponse[List[NewsItemSchema]])
def get_news_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None,
    business_category: Optional[str] = None,
    info_type: Optional[str] = None,
    status: Optional[str] = "published",
    min_quality_score: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    sort_by: str = "publish_date",
    sort_order: str = "desc",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取资讯列表"""
    query_params = NewsQuerySchema(
        page=page, page_size=page_size, keyword=keyword,
        business_category=business_category, info_type=info_type,
        status=status, min_quality_score=min_quality_score,
        start_date=start_date, end_date=end_date,
        sort_by=sort_by, sort_order=sort_order,
    )
    items, total = news_service.get_news_list(db, query_params)
    total_pages = (total + page_size - 1) // page_size

    return PageResponse(
        data=[NewsItemSchema.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{news_id}", response_model=DataResponse[NewsItemDetailSchema])
def get_news_detail(
    news_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取资讯详情"""
    news = news_service.get_news_detail(db, news_id)
    return DataResponse(data=NewsItemDetailSchema.model_validate(news))


@router.put("/{news_id}", response_model=DataResponse[NewsItemAdminSchema])
def update_news(
    news_id: str,
    obj_in: NewsItemUpdateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("editor")),
):
    """更新资讯（编辑/管理员）"""
    news = news_service.get(db, news_id)
    if not news:
        return DataResponse(code=404, message="资讯不存在")

    updated = news_service.update(db, db_obj=news, obj_in=obj_in)
    return DataResponse(data=NewsItemAdminSchema.model_validate(updated))


@router.post("/{news_id}/audit", response_model=DataResponse[NewsItemAdminSchema])
def audit_news(
    news_id: str,
    status: str = Query(..., description="审核状态: published/rejected"),
    comment: str = Query("", description="审核意见"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("reviewer")),
):
    """审核资讯（审核员/管理员）"""
    news = news_service.audit_news(db, news_id, status, comment, str(current_user.id))
    return DataResponse(data=NewsItemAdminSchema.model_validate(news))


# ==================== 标签相关 ====================

@router.get("/tags/all", response_model=DataResponse[dict])
def get_all_tags(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取所有标签（按类型分组）"""
    tags = tag_service.get_all_tags(db)
    return DataResponse(data=tags)


@router.get("/tags/{tag_type}", response_model=ListResponse[TagSchema])
def get_tags_by_type(
    tag_type: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """按类型获取标签"""
    tags = tag_service.get_tags_by_type(db, tag_type)
    return ListResponse(data=[TagSchema.model_validate(t) for t in tags])


# ==================== 专题相关 ====================

@router.get("/topics/list", response_model=ListResponse[TopicSchema])
def get_topics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取专题列表"""
    topics = topic_service.get_active_topics(db)
    return ListResponse(data=[TopicSchema.model_validate(t) for t in topics])


@router.get("/topics/{topic_id}/news", response_model=PageResponse[List[NewsItemSchema]])
def get_topic_news(
    topic_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取专题下的资讯列表"""
    items, total = topic_service.get_topic_news(db, topic_id, page, page_size)
    total_pages = (total + page_size - 1) // page_size

    return PageResponse(
        data=[NewsItemSchema.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
