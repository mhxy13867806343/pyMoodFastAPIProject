from enum import Enum, IntEnum
import time
import uuid
def generate_uid():
    """生成32位的UID"""
    return str(uuid.uuid4()).replace('-', '')[:32]

def generate_default_name():
    """生成默认用户名：使用时间戳"""
    return f"user_{int(time.time())}"

class UserSex(IntEnum):
    """用户性别枚举"""
    UNKNOWN = 0  # 未知
    MALE = 1     # 男
    FEMALE = 2   # 女

class UserType(IntEnum):
    """用户类型枚举"""
    NORMAL = 0   # 普通用户
    ADMIN = 1    # 管理员
    SUPER = 2    # 超级管理员

class UserStatus(IntEnum):
    """用户状态枚举"""
    NORMAL = 0   # 正常
    DISABLED = 1 # 禁用
class DictStatus(IntEnum):
    """用户状态枚举"""
    NORMAL = 0   # 正常
    DISABLED = 1 # 禁用
class EmailStatus(IntEnum):
    """邮箱绑定状态枚举"""
    UNBOUND = 0    # 未绑定
    BOUND = 1      # 已绑定
    ERROR = 2      # 绑定异常

class LoginType(IntEnum):
    """登录方式枚举"""
    EMAIL = 0      # 邮箱登录
    USERNAME = 1   # 用户名登录
    PHONE = 2      # 手机号登录