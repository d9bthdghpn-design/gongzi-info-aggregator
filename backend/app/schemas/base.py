"""
Schema - 通用Schema
"""
import uuid
from datetime import datetime
from typing import Generic, TypeVar, Optional, List, Any
from pydantic import BaseModel, Field, model_validator


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

    @model_validator(mode='before')
    @classmethod
    def convert_uuid_fields(cls, data: Any):
        """将ORM对象或字典中的UUID字段自动转换为字符串，兼容PostgreSQL UUID类型"""
        if isinstance(data, dict):
            return {k: str(v) if isinstance(v, uuid.UUID) else v for k, v in data.items()}

        # 处理SQLAlchemy ORM对象：把__dict__中非SA内部的标量值拷贝，UUID转字符串
        if hasattr(data, '__dict__'):
            result = {}
            for key, value in data.__dict__.items():
                if key.startswith('_sa_'):
                    continue
                if isinstance(value, uuid.UUID):
                    result[key] = str(value)
                else:
                    result[key] = value
            return result

        return data

    class Config:
        from_attributes = True
