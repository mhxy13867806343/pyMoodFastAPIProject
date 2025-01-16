import time
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter, Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, JSONResponse
from extend.db import Base, ENGIN
from tool.appMount import staticMount
from tool.appRate import appLimitRate
from tool.appAddMiddleware import appAddMiddleware
from sqlalchemy.exc import SQLAlchemyError
from tool.dbRedis import RedisDB, check_redis
from fastapi.exceptions import RequestValidationError

import uvicorn
from app.users.views import userApp as userAppRouterApi
from app.dicts.views import dictApp as dictAppRouterApi
from tool.classDb import HttpStatus
from tool.getLogger import globalLogger
from config.error_messages import SYSTEM_ERROR

# 生命周期事件
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期事件处理"""
    # 启动事件
    try:
        # 检查 Redis 连接
        redis_status = check_redis()
        if redis_status["code"] != 200:
            globalLogger.error(SYSTEM_ERROR['REDIS_ERROR'])
            raise Exception(SYSTEM_ERROR['REDIS_ERROR'])
            
        # 初始化数据库
        try:
            Base.metadata.create_all(bind=ENGIN)
            globalLogger.info(SYSTEM_ERROR['DB_INIT_SUCCESS'])
        except Exception as e:
            globalLogger.error(f"{SYSTEM_ERROR['DB_INIT_ERROR']}: {str(e)}")
            raise
        yield
    finally:
        # 关闭事件
        globalLogger.info("应用正在关闭...")

# 创建主应用
app = FastAPI(lifespan=lifespan)

# 创建带全局前缀的路由器
v1_router = APIRouter(prefix="/v1")

# 将各个模块的路由添加到带前缀的路由器
v1_router.include_router(userAppRouterApi, prefix="/user")
v1_router.include_router(dictAppRouterApi, prefix="/dict")

# 将带有前缀的路由器添加到主应用
app.include_router(v1_router)

# 全局异常处理
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """处理请求参数验证错误"""
    globalLogger.error(f"{SYSTEM_ERROR['PARAM_ERROR']}: {str(exc.errors())}")
    return JSONResponse(
        status_code=status.HTTP_200_OK,  
        content={
            "code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "message": SYSTEM_ERROR['PARAM_ERROR'],
            "data": {"detail": str(exc.errors())}  
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """处理所有未捕获的异常"""
    error_msg = str(exc)  
    globalLogger.exception(f"{SYSTEM_ERROR['SERVER_ERROR']}: {error_msg}")
    return JSONResponse(
        status_code=status.HTTP_200_OK,  
        content={
            "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": SYSTEM_ERROR['SERVER_ERROR'],
            "data": {"detail": error_msg}  
        }
    )

# 请求日志和响应处理中间件
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # 记录请求信息
        globalLogger.info(f"Request: {request.method} {request.url}")
        globalLogger.info(f"Headers: {request.headers}")
        
        try:
            response = await call_next(request)
            
            # 记录响应时间
            process_time = time.time() - start_time
            globalLogger.info(f"Response time: {process_time:.3f}s")
            
            return response
        except Exception as e:
            globalLogger.exception(f"{SYSTEM_ERROR['REQUEST_ERROR']}:", e)
            raise

class CustomHeaderMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response: Response = await call_next(request)
            response.headers['X-Frame-Options'] = 'ALLOW-FROM https://lcs200.icu/#/'
            response.headers['Content-Security-Policy'] = "frame-ancestors 'self' https://lcs200.icu/#/"
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            return response
        except SQLAlchemyError as e:
            error_msg = str(e)
            globalLogger.exception(f"{SYSTEM_ERROR['DB_ERROR']}: {error_msg}")
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "message": SYSTEM_ERROR['DB_ERROR'],
                    "data": {"detail": error_msg}
                }
            )
        except Exception as e:
            error_msg = str(e)
            globalLogger.exception(f"{SYSTEM_ERROR['REQUEST_ERROR']}: {error_msg}")
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "message": SYSTEM_ERROR['REQUEST_ERROR'],
                    "data": {"detail": error_msg}
                }
            )

# 添加中间件（顺序很重要）
app.add_middleware(LoggingMiddleware)  # 首先添加日志中间件
appAddMiddleware(app)  # 然后是 CORS
app.add_middleware(CustomHeaderMiddleware)  # 最后是自定义头部

# 静态文件和限流
staticMount(app)
appLimitRate(app)

if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)
