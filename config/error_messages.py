from enum import Enum

class ErrorCode(Enum):
    """错误码枚举"""
    SUCCESS = 200
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    VALIDATION_ERROR = 422
    TOO_MANY_REQUESTS = 429
    INTERNAL_ERROR = 500
    DB_ERROR = 501
    REDIS_ERROR = 502

"""
错误信息配置
"""

# 系统错误信息
SYSTEM_ERROR = {
    "PARAM_ERROR": "参数验证错误",
    "SERVER_ERROR": "服务器内部错误",
    "DB_ERROR": "数据库操作出现异常",
    "REDIS_ERROR": "Redis连接失败",
    "REQUEST_ERROR": "请求处理出现异常",
    "DB_INIT_ERROR": "数据库初始化失败",
    "DB_INIT_SUCCESS": "数据库初始化成功",
    "CONFIG_ERROR": "配置错误：未找到必须的环境变量"
}

# 用户相关错误信息
USER_ERROR = {
    "NOT_FOUND": "用户不存在",
    "ALREADY_EXISTS": "用户已存在",
    "PASSWORD_ERROR": "密码错误",
    "TOKEN_EXPIRED": "登录已过期",
    "TOKEN_INVALID": "无效的登录信息",
    "TOKEN_CREATE_ERROR": "创建登录令牌失败",
    "PERMISSION_DENIED": "权限不足"
}

# 业务相关错误信息
BUSINESS_ERROR = {
    "RATE_LIMIT": "请求过于频繁",
    "INVALID_OPERATION": "无效的操作",
    "RESOURCE_NOT_FOUND": "资源不存在",
    "DATA_VALIDATION_ERROR": "数据验证失败"
}
