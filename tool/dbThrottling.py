from datetime import datetime
from typing import Optional, Tuple

from slowapi.errors import RateLimitExceeded
from fastapi import Request, HTTPException, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi.responses import JSONResponse
from tool.getLogger import globalLogger

def get_client_info(request: Request) -> Tuple[str, Optional[str]]:
    """获取客户端信息"""
    ip = get_remote_address(request)
    user_agent = request.headers.get("user-agent", "Unknown")
    return ip, user_agent

# 创建限流器实例
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200/minute"]  # 默认限制：每分钟200次请求
)

# 不同路由的限制规则
ROUTE_LIMITS = {
    "/v1/h5/user/login": ["20/minute"],     # 登录接口限制
    "/v1/h5/user/register": ["10/minute"],  # 注册接口限制
    "/v1/h5/user/info": ["100/minute"]      # 用户信息接口限制
}

async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """处理请求超出限制的情况"""
    ip, user_agent = get_client_info(request)
    
    # 解析限制信息
    limit_parts = exc.detail.split(" ")
    time_unit = limit_parts[-1]
    time_value = limit_parts[-2]
    
    # 转换时间单位为中文
    unit_map = {
        "second": "秒",
        "minute": "分钟",
        "hour": "小时",
        "day": "天"
    }
    chinese_unit = unit_map.get(time_unit, time_unit)
    
    # 记录超限信息
    globalLogger.warning(
        f"请求限制触发 - IP: {ip}, User-Agent: {user_agent}, "
        f"Path: {request.url.path}, Method: {request.method}"
    )
    
    error_message = (
        f"请求过于频繁，请稍后再试！\n"
        f"来自 {request.headers.get('host')} 的请求被限制\n"
        f"限制时间: {time_value}{chinese_unit}\n"
        f"允许请求次数: {limit_parts[0]}次"
    )
    
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "code": status.HTTP_429_TOO_MANY_REQUESTS,
            "message": error_message,
            "data": {
                "retry_after": f"{time_value} {time_unit}",
                "limit": limit_parts[0]
            }
        },
        headers={
            "Retry-After": time_value,
            "X-RateLimit-Limit": limit_parts[0],
            "X-RateLimit-Reset": str(int(datetime.now().timestamp()) + int(time_value) * 60)
        }
    )