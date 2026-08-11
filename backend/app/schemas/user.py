"""
Schema - 用户相关
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr
from app.schemas.base import BaseSchema


class UserSchema(BaseSchema):
    """用户Schema"""
    username: str
    email: Optional[str] = None
    phone: Optional[str] = None
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    role: str = "viewer"
    is_active: bool = True
    last_login_at: Optional[datetime] = None


class UserCreateSchema(BaseModel):
    """创建用户Schema"""
    username: str
    email: Optional[str] = None
    phone: Optional[str] = None
    full_name: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    role: str = "viewer"


class UserUpdateSchema(BaseModel):
    """更新用户Schema"""
    email: Optional[str] = None
    phone: Optional[str] = None
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class LoginSchema(BaseModel):
    """登录Schema"""
    username: str
    password: str


class TokenSchema(BaseModel):
    """Token响应Schema"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserSchema


class RefreshTokenSchema(BaseModel):
    """刷新Token Schema"""
    refresh_token: str
