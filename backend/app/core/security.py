"""
核心安全模块 - JWT认证、密码哈希
"""
import hashlib
import base64
import os
from datetime import datetime, timedelta
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login")


def _hash_password_sha256(password: str, salt: str) -> str:
    """使用SHA256 + salt哈希密码"""
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码
    格式：salt$hash
    """
    try:
        salt, hash_val = hashed_password.split("$", 1)
        computed = _hash_password_sha256(plain_password, salt)
        return computed == hash_val
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    salt = base64.b64encode(os.urandom(16)).decode()
    hash_val = _hash_password_sha256(password, salt)
    return f"{salt}${hash_val}"


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问Token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """创建刷新Token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict:
    """解码Token"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except Exception:
        return {}


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        if user_id is None or token_type != "access":
            raise credentials_exception
    except Exception:
        raise credentials_exception
    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        raise credentials_exception
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """获取当前活跃用户"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="用户已被禁用")
    return current_user


def require_role(required_role: str):
    """角色权限装饰器"""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        role_hierarchy = {"viewer": 1, "reviewer": 2, "editor": 3, "admin": 4}
        if role_hierarchy.get(current_user.role, 0) < role_hierarchy.get(required_role, 99):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要 {required_role} 权限",
            )
        return current_user
    return role_checker
