from enum import IntEnum
from config import base_error_code

class ErrorMessages(IntEnum):
    """错误码枚举"""
    # 基础状态码
    SUCCESS = base_error_code.SUCCESS
    BAD_REQUEST = base_error_code.BAD_REQUEST
    UNAUTHORIZED = base_error_code.UNAUTHORIZED
    FORBIDDEN = base_error_code.FORBIDDEN
    NOT_FOUND = base_error_code.NOT_FOUND
    METHOD_NOT_ALLOWED = base_error_code.METHOD_NOT_ALLOWED
    VALIDATION_ERROR = base_error_code.VALIDATION_ERROR
    TOO_MANY_REQUESTS = base_error_code.TOO_MANY_REQUESTS
    INTERNAL_ERROR = base_error_code.INTERNAL_ERROR
    DB_ERROR = base_error_code.DB_ERROR
    REDIS_ERROR = base_error_code.REDIS_ERROR

"""
错误信息配置
"""

# 用户相关错误
USER_ERROR = {
    # Token相关错误
    "TOKEN_CREATE_ERROR": "创建token失败",
    "TOKEN_EXPIRED": "用户信息已过期,请重新登录",
    "TOKEN_INVALID": "无效的token",
    "TOKEN_MISSING": "缺少token",
    
    # 账号相关错误
    "ACCOUNT_OR_PASSWORD_ERROR": "账号或密码错误",
    "ACCOUNT_NOT_FOUND": "账号不存在",
    "ACCOUNT_EXISTS": "账号已存在",
    "ACCOUNT_NOT_EMAIL_FOUND": "邮箱/用户名 或者密码不能为空",
    "ACCOUNT_DISABLED": "账号已被禁用",
    "ACCOUNT_LOCKED": "账号已被锁定",
    "ACCOUNT_EXPIRED": "账号已过期",
    "ACCOUNT_DELETED": "账号已删除",
    
    # 邮箱相关错误
    "EMAIL_EXISTS": "邮箱已存在",
    "EMAIL_NOT_FOUND": "邮箱不存在",
    "EMAIL_FORMAT_ERROR": "邮箱格式错误",
    "EMAIL_INVALID_FORMAT": "邮箱格式不正确",
    "EMAIL_SEND_ERROR": "邮件发送失败",
    "EMAIL_SEND_FAILED": "邮件发送失败",
    "EMAIL_CODE_INVALID": "验证码错误或已过期",
    "EMAIL_CODE_EXPIRED": "验证码已过期",
    "EMAIL_CODE_FREQ_LIMIT": "验证码发送过于频繁，请稍后再试",
    "EMAIL_ALREADY_BOUND": "该邮箱已被其他用户绑定",
    "EMAIL_NOT_VERIFIED": "邮箱未验证",
    "EMAIL_VERIFY_CODE_ERROR": "验证码错误",
    "EMAIL_VERIFY_CODE_EXPIRED": "验证码已过期",
    "EMAIL_VERIFY_CODE_NOT_FOUND": "验证码不存在",
    
    # 密码相关错误
    "PASSWORD_ERROR": "密码错误",
    "PASSWORD_FORMAT_ERROR": "密码格式错误",
    "PASSWORD_NOT_MATCH": "两次输入的密码不一致",
    "PASSWORD_TOO_SHORT": "密码长度不能小于6位",
    "PASSWORD_TOO_SIMPLE": "密码过于简单",
    "PASSWORD_WEAK": "密码强度太弱，最少6位，包括至少1个大写字母，1个小写字母，1个数字，1个特殊字符",
    "PASSWORD_EMPTY": "密码不能为空",
    "PASSWORD_UPDATE_SUCCESS": "密码修改成功",
    "PASSWORD_UPDATE_FAILED": "密码修改失败",
    
    # 用户名相关错误
    "USERNAME_EXISTS": "用户名已存在",
    "USERNAME_NOT_FOUND": "用户名不存在",
    "USERNAME_INVALID": "用户名无效",
    "USERNAME_TOO_SHORT": "用户名太短",
    "USERNAME_TOO_LONG": "用户名太长",
    
    # 用户信息相关错误
    "USER_NOT_FOUND": "用户不存在",
    "USER_EXISTS": "当前帐号已存在，请直接登录",
    "USER_UPDATE_SUCCESS": "用户信息更新成功",
    "USER_UPDATE_FAILED": "用户信息更新失败",
    "USER_DELETE_SUCCESS": "用户删除成功",
    "USER_DELETE_FAILED": "用户删除失败",
    
    # 昵称相关错误
    "NICKNAME_EMPTY": "昵称不能为空",
    "NICKNAME_TOO_LONG": "昵称太长",
    "NICKNAME_INVALID": "昵称无效",
    "NICKNAME_EXISTS": "昵称已存在",
    "NICKNAME_NO_CHANGE": "昵称未发生变化",
    
    # 手机号相关错误
    "PHONE_EXISTS": "手机号已存在",
    "PHONE_NOT_FOUND": "手机号不存在",
    "PHONE_NOT_VERIFIED": "手机号未验证",
    "PHONE_VERIFY_CODE_ERROR": "验证码错误",
    "PHONE_VERIFY_CODE_EXPIRED": "验证码已过期",
    "PHONE_VERIFY_CODE_NOT_FOUND": "验证码不存在",
    "PHONE_SEND_ERROR": "短信发送失败",
    
    # 权限相关错误
    "PERMISSION_DENIED": "权限不足",
    "PERMISSION_ERROR": "权限错误",
    "PERMISSION_NOT_FOUND": "权限不存在",
    
    # 系统相关错误
    "SYSTEM_ERROR": "系统错误，请稍后再试",
    "NETWORK_ERROR": "网络错误，请检查网络连接",
    "SERVER_ERROR": "服务器错误",
    "REQUEST_ERROR": "请求错误",
    "PARAM_ERROR": "参数错误",
    "DATA_ERROR": "数据错误",
    "OPERATION_FAILED": "操作失败",
    "OPERATION_TOO_FREQUENT": "操作过于频繁，请稍后再试"
}

# 系统相关错误
SYSTEM_ERROR = {
    "SYSTEM_ERROR": "系统错误",
    "DATABASE_ERROR": "数据库错误",
    "REDIS_ERROR": "Redis错误",
    "NETWORK_ERROR": "网络错误",
    "TIMEOUT_ERROR": "超时错误",
    "PARAMETER_ERROR": "参数错误",
    "DB_ERROR": "数据库操作出现异常",
    "DB_INIT_ERROR": "数据库初始化失败",
    "DB_INIT_SUCCESS": "数据库初始化成功",
    "CONFIG_ERROR": "配置错误：未找到必须的环境变量",
    "PARAM_ERROR": "参数验证错误",
    "SERVER_ERROR": "服务器内部错误",
    "REQUEST_ERROR": "请求处理出现异常",
    "FILE_NOT_FOUND": "文件不存在",
    "FILE_TOO_LARGE": "文件太大",
    "FILE_TYPE_ERROR": "文件类型错误",
    "FILE_UPLOAD_ERROR": "文件上传失败",
    "FILE_DOWNLOAD_ERROR": "文件下载失败",
    "FILE_DELETE_ERROR": "文件删除失败",
    "FILE_SAVE_ERROR": "文件保存失败",
    "FILE_READ_ERROR": "文件读取失败",
    "FILE_WRITE_ERROR": "文件写入失败",
    "FILE_MOVE_ERROR": "文件移动失败",
    "FILE_COPY_ERROR": "文件复制失败",
    "FILE_RENAME_ERROR": "文件重命名失败",
    "FILE_EXISTS": "文件已存在",
    "DIRECTORY_NOT_FOUND": "目录不存在",
    "DIRECTORY_EXISTS": "目录已存在",
    "DIRECTORY_CREATE_ERROR": "目录创建失败",
    "DIRECTORY_DELETE_ERROR": "目录删除失败",
    "DIRECTORY_MOVE_ERROR": "目录移动失败",
    "DIRECTORY_COPY_ERROR": "目录复制失败",
    "DIRECTORY_RENAME_ERROR": "目录重命名失败"
}

# 业务相关错误
BUSINESS_ERROR = {
    "RATE_LIMIT": "请求过于频繁",
    "OPERATION_TOO_FREQUENT": "操作过于频繁",
    "OPERATION_NOT_ALLOWED": "操作不允许",
    "OPERATION_FAILED": "操作失败",
    "OPERATION_TIMEOUT": "操作超时",
    "OPERATION_CANCELLED": "操作已取消",
    "OPERATION_NOT_SUPPORTED": "操作不支持",
    "OPERATION_NOT_COMPLETED": "操作未完成",
    "OPERATION_ALREADY_COMPLETED": "操作已完成",
    "OPERATION_ALREADY_EXISTS": "操作已存在",
    "OPERATION_NOT_EXISTS": "操作不存在",
    "OPERATION_NOT_FOUND": "操作未找到",
    "OPERATION_NOT_VALID": "操作无效",
    "OPERATION_NOT_AUTHORIZED": "操作未授权",
    "OPERATION_NOT_PERMITTED": "操作不允许",
    "OPERATION_NOT_AVAILABLE": "操作不可用",
    "OPERATION_NOT_READY": "操作未就绪",
    "OPERATION_NOT_STARTED": "操作未开始",
    "OPERATION_NOT_STOPPED": "操作未停止",
    "OPERATION_NOT_PAUSED": "操作未暂停",
    "OPERATION_NOT_RESUMED": "操作未恢复",
    "OPERATION_NOT_RESTARTED": "操作未重启",
    "OPERATION_NOT_DELETED": "操作未删除",
    "OPERATION_NOT_UPDATED": "操作未更新",
    "OPERATION_NOT_CREATED": "操作未创建",
    "OPERATION_NOT_MODIFIED": "操作未修改",
    "OPERATION_NOT_SAVED": "操作未保存",
    "OPERATION_NOT_LOADED": "操作未加载",
    "OPERATION_NOT_INITIALIZED": "操作未初始化",
    "OPERATION_NOT_CONFIGURED": "操作未配置",
    "OPERATION_NOT_ENABLED": "操作未启用",
    "OPERATION_NOT_DISABLED": "操作未禁用",
    "OPERATION_NOT_LOCKED": "操作未锁定",
    "OPERATION_NOT_UNLOCKED": "操作未解锁",
    "OPERATION_NOT_VERIFIED": "操作未验证",
    "OPERATION_NOT_VALIDATED": "操作未验证",
    "OPERATION_NOT_PROCESSED": "操作未处理",
    "OPERATION_NOT_EXECUTED": "操作未执行",
    "OPERATION_NOT_FINISHED": "操作未完成",
    "OPERATION_NOT_ENDED": "操作未结束",
    "OPERATION_NOT_CLOSED": "操作未关闭",
    "OPERATION_NOT_OPENED": "操作未打开",
    "OPERATION_NOT_CONNECTED": "操作未连接",
    "OPERATION_NOT_DISCONNECTED": "操作未断开",
    "OPERATION_NOT_BOUND": "操作未绑定",
    "OPERATION_NOT_UNBOUND": "操作未解绑",
    "OPERATION_NOT_REGISTERED": "操作未注册",
    "OPERATION_NOT_UNREGISTERED": "操作未注销",
    "OPERATION_NOT_LOGGED_IN": "操作未登录",
    "OPERATION_NOT_LOGGED_OUT": "操作未登出",
    "OPERATION_NOT_SIGNED_IN": "操作未签入",
    "OPERATION_NOT_SIGNED_OUT": "操作未签出",
    "OPERATION_NOT_CHECKED_IN": "操作未签到",
    "OPERATION_NOT_CHECKED_OUT": "操作未签出"
}

# 认证相关错误
AUTH_ERROR = {
    "TOKEN_EXPIRED": {
        "code": 401001,
        "msg": "用户信息已过期",
        "status_code": 401
    },
    "TOKEN_INVALID": {
        "code": 401002,
        "msg": "无效的认证信息",
        "status_code": 401
    },
    "TOKEN_MISSING": {
        "code": 401003,
        "msg": "缺少认证信息",
        "status_code": 401
    }
}

# 导出所有错误信息
__all__ = ["USER_ERROR", "SYSTEM_ERROR", "BUSINESS_ERROR", "AUTH_ERROR"]
