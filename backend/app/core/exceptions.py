"""
核心模块 - 异常处理
"""
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException


class BusinessException(Exception):
    """业务异常"""
    def __init__(self, code: int = 400, message: str = "业务异常", data=None):
        self.code = code
        self.message = message
        self.data = data


async def business_exception_handler(request: Request, exc: BusinessException):
    """业务异常处理器"""
    return JSONResponse(
        status_code=200,
        content={
            "code": exc.code,
            "message": exc.message,
            "data": exc.data,
        },
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """HTTP异常处理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code,
            "message": exc.detail,
            "data": None,
        },
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """参数验证异常处理器"""
    return JSONResponse(
        status_code=422,
        content={
            "code": 422,
            "message": "参数验证失败",
            "data": exc.errors(),
        },
    )


async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理器"""
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": "服务器内部错误",
            "data": None,
        },
    )
