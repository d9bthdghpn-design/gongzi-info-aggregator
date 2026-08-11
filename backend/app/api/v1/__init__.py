"""
API v1 路由汇总
"""
from fastapi import APIRouter
from app.api.v1.news import router as news_router
from app.api.v1.leads import router as leads_router
from app.api.v1.users import router as auth_router, router_users as users_router
from app.api.v1.briefings import router as briefings_router

api_router = APIRouter()

# 资讯相关
api_router.include_router(news_router)

# 线索相关
api_router.include_router(leads_router)

# 用户认证与管理
api_router.include_router(auth_router)
api_router.include_router(users_router)

# 简报相关
api_router.include_router(briefings_router)
