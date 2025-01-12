from pydantic import BaseModel, validator
from typing import Optional
from tool.dbEnum import UserSex, LoginType
import re

class UserAuth(BaseModel):
    """用户认证模型"""
    account: str  # 登录账号（邮箱或用户名）
    password: str
    login_type: LoginType = LoginType.EMAIL  # 默认使用邮箱登录

class UserInfo(BaseModel):
    """用户信息模型"""
    uid: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    sex: Optional[UserSex] = None
    code: Optional[str] = None  # 验证码，可选
    username: Optional[str] = None
    password: Optional[str] = None  # 用户密码
    avatar: Optional[str] = None  # 用户头像
    is_registered: Optional[int] = None  # 注册状态
    signature: Optional[str] = None  # 注册状态

    @validator('phone')
    def validate_phone(cls, v):
        if v and not v.isdigit():
            raise ValueError('手机号必须是数字')
        if v and len(v) != 11:
            raise ValueError('手机号长度必须是11位')
        return v
    
    @validator('email')
    def validate_email(cls, v):
        if v:
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(pattern, v):
                raise ValueError('邮箱格式不正确')
        return v
