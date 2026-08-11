"""
Schema - 通用Schema
"""
from datetime import datetime
from typing import Generic, TypeVar, Optional, List
from pydantic import BaseModel, Field

T = TypeVar("T")


class ResponseBase(BaseModel):
    """统一响应基类"""
    code: int = 0
    message: str = "success"


class PageResponse(ResponseBase, Generic[T]):
    """分页响应"""
    data: Optional[T] = None
    total: int = 0
    page: int = 1
    page_size: int = 20
    total_pages: int = 0


class DataResponse(ResponseBase, Generic[T]):
    """单数据响应"""
    data: Optional[T] = None


class ListResponse(ResponseBase, Generic[T]):
    """列表响应"""
    data: List[T] = []


class BaseSchema(BaseModel):
    """基础Schema"""
    id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
