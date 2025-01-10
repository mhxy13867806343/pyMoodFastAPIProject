import time
from datetime import datetime

from fastapi import FastAPI, APIRouter,Request,status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from extend.db import Base, ENGIN # 导入数据库相关模块
from tool.appMount import staticMount
from tool.appRate import appLimitRate
from tool.appAddMiddleware import appAddMiddleware
from sqlalchemy.exc import SQLAlchemyError

import uvicorn
from app.users.views import userApp as userAppRouterApi
from tool.classDb import httpStatus
from tool.getLogger import globalLogger

# 创建主应用
app = FastAPI()

# 创建带全局前缀的路由器
v1_router = APIRouter(prefix="/v1")

# 将各个模块的路由添加到带前缀的路由器
v1_router.include_router(userAppRouterApi, prefix="/h5/user", tags=["用户管理"])

# 将带有前缀的路由器添加到主应用
app.include_router(v1_router)
# 中间件和其他配置
class CustomHeaderMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response: Response = await call_next(request)
            response.headers['X-Frame-Options'] = 'ALLOW-FROM https://lcs200.icu/#/'
            response.headers['Content-Security-Policy'] = "frame-ancestors 'self' https://lcs200.icu/#/"
            return response
        except SQLAlchemyError as e:
            globalLogger.exception("数据库操作出现异常:",e)
            return httpStatus(code=status.HTTP_500_INTERNAL_SERVER_ERROR, message="数据库操作出现异常")
        except Exception as e:
            globalLogger.exception("请求处理出现异常:",e)
            return httpStatus(code=status.HTTP_500_INTERNAL_SERVER_ERROR, message="请求处理出现异常")
# 添加CORS和自定义中间件
appAddMiddleware(app)
app.add_middleware(CustomHeaderMiddleware)

# 静态文件和限流
staticMount(app)
appLimitRate(app)

# 初始化数据库
Base.metadata.create_all(bind=ENGIN)

if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)
