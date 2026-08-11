"""
Schema - 简报相关
"""
from datetime import date
from typing import Optional, List, Dict
from pydantic import BaseModel
from app.schemas.base import BaseSchema


class DailyBriefingSchema(BaseSchema):
    """每日简报Schema"""
    brief_date: date
    area_scope: Optional[str] = None
    content_json: dict = {}
    total_count: int = 0
    category_counts: dict = {}
    is_pushed: bool = False
    pushed_at: Optional[str] = None


class BriefingCategoryItem(BaseModel):
    """简报分类项"""
    category_code: str
    category_name: str
    icon: str
    count: int
    items: List[dict] = []


class BriefingGenerateSchema(BaseModel):
    """生成简报Schema"""
    brief_date: Optional[date] = None
    area_scope: Optional[str] = None
