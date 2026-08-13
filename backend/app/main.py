"""
对公资讯聚合系统 - FastAPI主应用
"""
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager
from sqlalchemy import text

from app.config import settings
from app.database import engine, Base, SessionLocal
from app.api import api_router
from app.core.exceptions import (
    BusinessException,
    business_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} 启动中...")
    # 开发环境自动建表（生产环境用 Alembic）
    if settings.ENVIRONMENT != "production":
        Base.metadata.create_all(bind=engine)
    yield
    print(f"👋 {settings.APP_NAME} 关闭")


# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="面向银行对公业务条线的公开资讯智能监测与商机挖掘平台",
    lifespan=lifespan,
)

# CORS中间件
_cors_origins = settings.CORS_ORIGINS
# 通配符 origin 不能与 allow_credentials 同时使用
_allow_credentials = "*" not in _cors_origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 异常处理器
app.add_exception_handler(BusinessException, business_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# 注册API路由
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["系统"])
def health_check():
    """健康检查（含数据库连通性）"""
    db_ok = False
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        db_ok = True
    except Exception:
        db_ok = False

    status = "ok" if db_ok else "degraded"
    return JSONResponse(
        status_code=200 if db_ok else 503,
        content={
            "status": status,
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "database": "ok" if db_ok else "error",
        },
    )


# 挂载静态文件（前端生产构建产物）
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/assets", StaticFiles(directory=os.path.join(static_dir, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def spa_fallback(request: Request, full_path: str):
        """SPA单页应用路由回退，所有非API路径都返回index.html"""
        if full_path.startswith("api/") or full_path.startswith("docs") or full_path.startswith("openapi.json"):
            raise StarletteHTTPException(status_code=404, detail="Not Found")

        index_file = os.path.join(static_dir, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"message": "前端文件未找到，请先构建前端"}


@app.get("/", tags=["系统"])
def root():
    """根路径"""
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "api_prefix": settings.API_V1_PREFIX,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
