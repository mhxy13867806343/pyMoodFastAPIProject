from fastapi import FastAPI,status,Request

from tool.classDb import httpStatus

app = FastAPI()
@app.middleware("http")
async def allow_pc_only(request: Request, call_next):
    if not request.url.path.startswith("/h5/"):
        user_agent = request.headers.get('User-Agent', '').lower()
        if 'mobile' in user_agent or 'android' in user_agent or 'iphone' in user_agent:
            # 如果检测到是移动设备且不是访问/h5/路径，返回403禁止访问
            return httpStatus(code=status.HTTP_403_FORBIDDEN,message="当前环境不允许进行访问", data={})
        # 对于/h5/路径或非移动设备请求，继续处理
    response = await call_next(request)
    return response