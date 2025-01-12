from enum import Enum
from typing import Dict, NamedTuple

class ApiDescription(NamedTuple):
    """API 描述信息"""
    description: str
    summary: str

class ApiDescriptions:
    """API 描述配置"""
    
    # 用户认证相关
    AUTH = {
        "summary": "用户认证",
        "description": """用户认证接口：处理注册和登录
- 优先从 Redis 缓存获取用户信息
- 支持邮箱和用户名两种登录方式
- 如果用户不存在，则注册新用户并自动登录
- 如果用户存在，则验证密码进行登录
- 记录登录信息到 MySQL 和 Redis
- 处理连续登录天数（断签重置为1天）
- 特殊处理管理员账号
"""
    }

    # 用户信息相关
    GET_USER_INFO = {
        "summary": "获取当前用户信息",
        "description": """获取当前登录用户的详细信息
- 从 token 中获取用户 ID
- 返回用户的所有可见信息
"""
    }

    GET_USER_INFO_BY_ID = {
        "summary": "获取指定用户信息",
        "description": """获取指定用户的公开信息
- 如果是获取自己的信息，返回所有信息
- 如果是获取其他用户的信息，只返回公开信息
- 如果未登录，只返回最基本的公开信息
"""
    }

    UPDATE_USER = {
        "summary": "更新用户信息",
        "description": """更新用户信息
- 需要登录
- 只能更新自己的信息
- 支持更新：昵称、性别、头像、位置、签名
"""
    }

    # 登录登出相关
    LOGOUT = {
        "summary": "用户登出",
        "description": """用户登出
- 需要登录
- 清除 Redis 缓存
- 更新最后登录时间
"""
    }

    # 邮箱相关
    BIND_EMAIL = {
        "summary": "绑定邮箱",
        "description": """绑定用户邮箱
- 需要登录
- 需要验证码
"""
    }

    SEND_EMAIL_CODE = {
        "summary": "发送邮箱验证码",
        "description": """发送邮箱验证码
- 需要登录
"""
    }

    # 文件上传相关
    UPLOAD_AVATAR = {
        "summary": "上传头像",
        "description": """上传用户头像
- 支持图片格式：.png、.jpg、.jpeg、.webp
- 文件大小限制：10MB
"""
    }

    BATCH_UPLOAD = {
        "summary": "批量上传文件",
        "description": """批量上传文件
- 支持图片格式：.png、.jpg、.jpeg、.webp（最多9张）
- 支持视频格式：.mp4、.mov、.avi（最多1个）
- 图片大小限制：10MB
- 视频大小限制：100MB
"""
    }

    # 签名相关
    GET_USER_SIGNATURE = {
        "summary": "获取用户签名",
        "description": """获取当前用户的签名
- 需要登录
- 只返回当前用户的签名信息
"""
    }

    SET_USER_SIGNATURE = {
        "summary": "设置用户签名",
        "description": """设置当前用户的签名
- 需要登录
- 签名长度限制：200字
"""
    }
