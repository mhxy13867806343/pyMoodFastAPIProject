from enum import Enum
from typing import Dict, NamedTuple

class ApiDescription(NamedTuple):
    """API 描述信息"""
    description: str
    summary: str

class ApiDescriptions:
    """API 描述配置"""
    USER_TAGS="用户相关"
    DICT_TAGS="字典管理"
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
- 签名长度限制：32字
"""
    }
    POST_USER_CHECK_NAME={
        "summary": "检查用户名是否可用",
        "description": """检查指定的用户名是否可用，如果不可用则返回建议的用户名列表
    """
    }
    PUT_USER_CHANGE_NAME_={
        "summary": "修改用户名称",
        "description": """修改当前用户的显示名称
      """
    }

    GET_USER_LEVEL_ = {
        "summary": "获取用户等级信息",
        "description": """
        获取当前登录用户的等级信息，包括：
        - 当前等级
        - 最大等级
        - 当前经验值
        - 下一级所需经验值
        - 距离下一级还需要的经验值
        """
    }

    PUT_USER_EXP_ = {
        "summary": "更新用户经验值",
        "description": """
        增加用户的经验值，并返回更新后的等级信息：
        - 支持增加指定数量的经验值
        - 自动计算是否升级
        - 返回更新后的等级信息
        """
    }
    # 字典相关
    DICT_GET_DESC = {
        "summary": "获取字典列表",
        "description": """获取字典列表
- 支持按名称、类型、状态筛选
- 默认只返回正常状态的字典
- 分页返回结果"""
    }

    DICT_GET_BY_ID_DESC = {
        "summary": "获取字典详情",
        "description": """获取单个字典的详细信息
- 只能获取正常状态的字典
- 返回字典的所有信息"""
    }

    DICT_POST_DESC = {
        "summary": "创建字典",
        "description": """创建新的字典
- 字典名称和key不能重复
- 默认为正常状态"""
    }

    DICT_PUT_DESC = {
        "summary": "更新字典",
        "description": """更新字典信息
- 禁用状态的字典不能修改
- 字典名称和key不能与其他字典重复"""
    }

    DICT_STATUS_DESC = {
        "summary": "更新字典状态",
        "description": """更新字典的状态
- 可以启用或禁用字典
- status=0 表示正常
- status=1 表示禁用"""
    }

    DICT_CODE_DESC = {
        "summary": "获取字典详情",
        "description": """获取指定字典的详细信息"""
    }
    DICT_DEL_DESC = {
        "summary": "删除字典",
        "description": """删除指定的字典"""
    }
    DICT_ITEMS_GET_DESC = {
        "summary": "获取字典项列表",
        "description": """获取指定字典下的所有字典项"""
    }
    DICT_ITEM_POST_DESC = {
        "summary": "创建字典项",
        "description": """在指定字典下创建新的字典项"""
    }
    DICT_ITEM_PUT_DESC = {
        "summary": "更新字典项",
        "description": """更新指定的字典项信息"""
    }
    DICT_ITEM_DEL_DESC = {
        "summary": "删除字典项",
        "description": """删除指定的字典项"""
    }