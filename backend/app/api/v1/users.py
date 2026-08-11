"""
用户API - 认证、用户管理
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.core.security import get_current_user, require_role
from app.schemas.user import (
    UserSchema, UserCreateSchema, UserUpdateSchema,
    LoginSchema, TokenSchema, RefreshTokenSchema,
)
from app.schemas.base import DataResponse, ListResponse
from app.services import user_service

router = APIRouter(prefix="/auth", tags=["用户认证"])


@router.post("/login", response_model=DataResponse[TokenSchema])
def login(
    obj_in: LoginSchema,
    db: Session = Depends(get_db),
):
    """用户登录"""
    token = user_service.login(db, obj_in.username, obj_in.password)
    return DataResponse(data=token)


@router.post("/refresh", response_model=DataResponse[TokenSchema])
def refresh_token(
    obj_in: RefreshTokenSchema,
    db: Session = Depends(get_db),
):
    """刷新Token"""
    token = user_service.refresh_token(db, obj_in.refresh_token)
    return DataResponse(data=token)


@router.get("/me", response_model=DataResponse[UserSchema])
def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    """获取当前用户信息"""
    return DataResponse(data=UserSchema.model_validate(current_user))


router_users = APIRouter(prefix="/users", tags=["用户管理"])


@router_users.get("", response_model=ListResponse[UserSchema])
def get_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """获取用户列表（管理员）"""
    from sqlalchemy import desc
    users = db.query(User).order_by(desc(User.created_at)).all()
    return ListResponse(data=[UserSchema.model_validate(u) for u in users])


@router_users.post("", response_model=DataResponse[UserSchema])
def create_user(
    obj_in: UserCreateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """创建用户（管理员）"""
    user = user_service.create(db, obj_in=obj_in)
    return DataResponse(data=UserSchema.model_validate(user))


@router_users.put("/{user_id}", response_model=DataResponse[UserSchema])
def update_user(
    user_id: str,
    obj_in: UserUpdateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """更新用户（管理员）"""
    user = user_service.get(db, user_id)
    if not user:
        return DataResponse(code=404, message="用户不存在")

    updated = user_service.update(db, db_obj=user, obj_in=obj_in)
    return DataResponse(data=UserSchema.model_validate(updated))
