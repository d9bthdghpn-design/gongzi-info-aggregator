"""
用户服务 - 用户认证与管理
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.orm import Session

from app.models import User
from app.schemas.user import UserCreateSchema, UserUpdateSchema, TokenSchema
from app.services.base import CRUDBase
from app.core.security import (
    verify_password, get_password_hash,
    create_access_token, create_refresh_token, decode_token,
)
from app.core.exceptions import BusinessException
from app.config import settings


class UserService(CRUDBase[User, UserCreateSchema, UserUpdateSchema]):
    """用户服务"""

    def __init__(self):
        super().__init__(User)

    def get_by_username(self, db: Session, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        return db.query(User).filter(User.username == username).first()

    def authenticate(self, db: Session, username: str, password: str) -> Optional[User]:
        """用户认证：校验数据库中的密码哈希"""
        user = self.get_by_username(db, username)
        if not user or not user.is_active:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

    def login(self, db: Session, username: str, password: str) -> TokenSchema:
        """登录"""
        user = self.authenticate(db, username, password)
        if not user:
            raise BusinessException(code=401, message="用户名或密码错误")

        if not user.is_active:
            raise BusinessException(code=403, message="用户已被禁用")

        # 更新最后登录时间
        user.last_login_at = datetime.now(timezone.utc)
        db.commit()

        # 生成Token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id), "username": user.username, "role": user.role},
            expires_delta=access_token_expires,
        )
        refresh_token = create_refresh_token(
            data={"sub": str(user.id), "username": user.username}
        )

        from app.schemas.user import UserSchema
        return TokenSchema(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserSchema.model_validate(user),
        )

    def refresh_token(self, db: Session, refresh_token: str) -> TokenSchema:
        """刷新Token"""
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise BusinessException(code=401, message="无效的刷新令牌")

        user_id = payload.get("sub")
        user = self.get(db, user_id)
        if not user or not user.is_active:
            raise BusinessException(code=401, message="用户不存在或已被禁用")

        # 生成新的访问Token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id), "username": user.username, "role": user.role},
            expires_delta=access_token_expires,
        )

        from app.schemas.user import UserSchema
        return TokenSchema(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserSchema.model_validate(user),
        )

    def sso_login(self, db: Session, provider: str, openid: str, user_info: dict) -> TokenSchema:
        """SSO登录"""
        # 查找已有用户
        user = db.query(User).filter(
            User.sso_provider == provider,
            User.sso_openid == openid,
        ).first()

        # 不存在则创建
        if not user:
            user = User(
                username=user_info.get("username", f"{provider}_{openid}"),
                full_name=user_info.get("full_name", ""),
                email=user_info.get("email", ""),
                avatar_url=user_info.get("avatar", ""),
                department=user_info.get("department", ""),
                position=user_info.get("position", ""),
                role="viewer",
                sso_provider=provider,
                sso_openid=openid,
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        # 更新最后登录时间
        user.last_login_at = datetime.now(timezone.utc)
        db.commit()

        # 生成Token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id), "username": user.username, "role": user.role},
            expires_delta=access_token_expires,
        )
        refresh_token = create_refresh_token(
            data={"sub": str(user.id), "username": user.username}
        )

        from app.schemas.user import UserSchema
        return TokenSchema(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserSchema.model_validate(user),
        )


# 服务单例
user_service = UserService()
