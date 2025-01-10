from enum import Enum

class UserIdentifier(Enum):
    """用户标识枚举"""
    CURRENT_USER = "10001"    # 当前用户
    OTHER_USER = "10002"      # 其他用户
    GUEST = "10003"          # 游客（未登录）
    ADMIN = "10004"          # 管理员
    SUPER_ADMIN = "10005"    # 超级管理员
