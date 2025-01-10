from enum import Enum
from typing import Dict, NamedTuple

class ApiDescription(NamedTuple):
    """API 描述信息"""
    description: str
    summary: str

class ApiDescriptions:
    """API 描述配置"""
    
    # 认证相关
    AUTH = ApiDescription(
        description="用户认证（登录/注册）",
        summary="用户认证"
    )
    LOGIN = ApiDescription(
        description="用户登录",
        summary="用户登录"
    )
    LOGOUT = ApiDescription(
        description="用户登出",
        summary="用户登出"
    )
    REGISTER = ApiDescription(
        description="用户注册",
        summary="用户注册"
    )
    
    # 用户相关
    UPDATE_USER_INFO = ApiDescription(
        description="更新用户信息",
        summary="更新用户信息"
    )
    GET_USER_INFO = ApiDescription(
        description="获取用户信息",
        summary="获取用户信息"
    )
    
    # 邮箱相关
    SEND_EMAIL_CODE = ApiDescription(
        description="发送邮箱验证码",
        summary="发送邮箱验证码"
    )
    BIND_EMAIL = ApiDescription(
        description="绑定邮箱地址",
        summary="绑定邮箱"
    )
    VERIFY_EMAIL = ApiDescription(
        description="验证邮箱验证码",
        summary="验证邮箱"
    )
