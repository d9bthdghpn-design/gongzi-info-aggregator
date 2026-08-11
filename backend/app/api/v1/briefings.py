"""
简报API - 每日简报生成、获取、推送
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import date, datetime
from typing import Optional, List

from app.database import get_db
from app.models import User
from app.core.security import get_current_user, require_role
from app.schemas.briefing import DailyBriefingSchema, BriefingGenerateSchema
from app.schemas.base import DataResponse, ListResponse
from app.services import briefing_service

router = APIRouter(prefix="/briefings", tags=["每日简报"])


@router.get("/today", response_model=DataResponse[DailyBriefingSchema])
def get_today_briefing(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取今日简报"""
    today = date.today()
    briefing = briefing_service.get_briefing_by_date(db, today)
    if not briefing:
        # 如果今日简报不存在，自动生成
        briefing = briefing_service.generate_briefing(db, today)
    return DataResponse(data=DailyBriefingSchema.model_validate(briefing))


@router.get("/{brief_date}", response_model=DataResponse[DailyBriefingSchema])
def get_briefing_by_date(
    brief_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """按日期获取简报"""
    briefing = briefing_service.get_briefing_by_date(db, brief_date)
    if not briefing:
        return DataResponse(code=404, message="该日期简报不存在")
    return DataResponse(data=DailyBriefingSchema.model_validate(briefing))


@router.post("/generate", response_model=DataResponse[DailyBriefingSchema])
def generate_briefing(
    obj_in: BriefingGenerateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("editor")),
):
    """生成简报（编辑/管理员）"""
    briefing = briefing_service.generate_briefing(
        db, obj_in.brief_date, obj_in.area_scope
    )
    return DataResponse(data=DailyBriefingSchema.model_validate(briefing))


@router.post("/{briefing_id}/push", response_model=DataResponse[DailyBriefingSchema])
def push_briefing(
    briefing_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("editor")),
):
    """推送简报（编辑/管理员）"""
    briefing = briefing_service.push_briefing(db, briefing_id)
    return DataResponse(data=DailyBriefingSchema.model_validate(briefing))


@router.get("/list/recent", response_model=ListResponse[DailyBriefingSchema])
def get_recent_briefings(
    limit: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取最近的简报列表"""
    briefings = briefing_service.get_latest_briefings(db, limit)
    return ListResponse(data=[DailyBriefingSchema.model_validate(b) for b in briefings])
