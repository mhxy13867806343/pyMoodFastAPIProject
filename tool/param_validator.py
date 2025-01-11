from functools import wraps
from typing import List, Optional, Any, Dict
from inspect import signature

from tool.msg import Message
from config.error_code import ErrorCode
from config.error_messages import USER_ERROR

def validate_params(*required_params: str):
    """
    装饰器：验证必需的参数
    :param required_params: 必需的参数名列表
    :return: 如果验证通过返回原函数结果，否则返回错误信息
    
    使用示例:
    @validate_params('user_id', 'username')
    async def update_user(user_id: int, username: str):
        ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取函数的参数信息
            sig = signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # 获取所有参数的值
            all_args = bound_args.arguments
            
            # 检查必需参数
            for param in required_params:
                value = all_args.get(param)
                if value is None:
                    return Message.error(
                        code=ErrorCode.PARAM_ERROR.value,
                        message=f"Parameter '{param}' is required"
                    )
                
                # 检查空字符串
                if isinstance(value, str) and not value.strip():
                    return Message.error(
                        code=ErrorCode.PARAM_ERROR.value,
                        message=f"Parameter '{param}' cannot be empty"
                    )
                
                # 检查空列表或字典
                if isinstance(value, (list, dict)) and not value:
                    return Message.error(
                        code=ErrorCode.PARAM_ERROR.value,
                        message=f"Parameter '{param}' cannot be empty"
                    )
                
                # 检查数字类型是否为0或负数（如果需要的话）
                if isinstance(value, (int, float)) and value <= 0:
                    return Message.error(
                        code=ErrorCode.PARAM_ERROR.value,
                        message=f"Parameter '{param}' must be greater than 0"
                    )
            
            # 所有验证通过，调用原函数
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator
