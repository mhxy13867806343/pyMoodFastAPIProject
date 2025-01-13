from pydantic import BaseModel, Field, field_validator
from typing import List
import re

class UserBase(BaseModel):
    username: str
    email: str | None = None
    password: str
    phone: str | None = None
    avatar: str | None = ""
    is_registered: int = 0

class UserUpdateRequest(BaseModel):
    """用户更新请求"""
    uid: str
    username: str | None = None
    email: str | None = None
    phone: str | None = None
    avatar: str | None = None
    name: str | None = None
    sex: int | None = None
    location: str | None = None
    code: str
    is_registered: int | None = None
    signature: str | None = None

    @field_validator('*')
    @classmethod
    def check_empty_string(cls, v, info):
        if isinstance(v, str) and not v.strip():
            raise ValueError(f"{info.field_name} cannot be empty")
        return v

    @field_validator('sex')
    @classmethod
    def check_sex(cls, v):
        if v not in [0, 1, 2]:  # 假设0=未知，1=男，2=女
            raise ValueError("Invalid sex value")
        return v

    @field_validator('email')
    @classmethod
    def check_email(cls, v):
        if not v or not '@' in v:
            raise ValueError("Invalid email format")
        # 简单的邮箱格式验证
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, v):
            raise ValueError("Invalid email format")
        return v

    @field_validator('phone')
    @classmethod
    def check_phone(cls, v):
        if not v.isdigit() or len(v) < 8:
            raise ValueError("Invalid phone number")
        return v

    @field_validator('signature')
    @classmethod
    def validate_signature(cls, v):
        if v and len(v) > 32:
            raise ValueError('签名不能超过32个字符')
        return v

class EmailBindRequest(BaseModel):
    email: str
    code: str

    @field_validator('email')
    @classmethod
    def check_email(cls, v):
        if not v or not '@' in v:
            raise ValueError("Invalid email format")
        # 简单的邮箱格式验证
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, v):
            raise ValueError("Invalid email format")
        return v

    @field_validator('code')
    @classmethod
    def check_code(cls, v):
        if not v.strip():
            raise ValueError("Verification code cannot be empty")
        return v

class EmailCodeRequest(BaseModel):
    email: str

    @field_validator('email')
    @classmethod
    def check_email(cls, v):
        if not v or not '@' in v:
            raise ValueError("Invalid email format")
        # 简单的邮箱格式验证
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, v):
            raise ValueError("Invalid email format")
        return v

class SignatureRequest(BaseModel):
    """签名请求"""
    signature: str | None = None

    @field_validator('signature')
    @classmethod
    def validate_signature(cls, v):
        if v and len(v) > 32:
            raise ValueError('签名不能超过32个字符')
        return v

class CheckNameRequest(BaseModel):
    """检查用户名是否可用的请求模型"""
    name: str = Field(..., description="要检查的用户名")

class CheckNameResponse(BaseModel):
    """检查用户名响应模型"""
    available: bool = Field(..., description="用户名是否可用")
    suggestions: List[str] = Field(default=[], description="如果用户名不可用，提供的建议名称列表")
