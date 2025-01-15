from pydantic import BaseModel, Field, field_validator
from typing import List, ForwardRef
import re

class DictBase(BaseModel):
    """字典基础模型"""
    name: str = Field(..., description="字典名称", max_length=50)
    key: str = Field(..., description="字典key", max_length=50)
    value: str = Field(..., description="字典value", max_length=50)
    type: str = Field(..., description="字典类型", max_length=50)

    @field_validator('*')
    @classmethod
    def check_empty_string(cls, v, info):
        if isinstance(v, str) and not v.strip():
            raise ValueError(f"{info.field_name} cannot be empty")
        return v.strip()

    @field_validator('key')
    @classmethod
    def validate_key(cls, v):
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', v):
            raise ValueError('key只能包含字母、数字和下划线，且必须以字母开头')
        return v

class DictCreate(DictBase):
    """创建字典请求模型"""
    pass

class DictUpdate(DictBase):
    """更新字典请求模型"""
    pass

class DictQuery(BaseModel):
    """字典查询参数"""
    page: int = Field(1, description="页码", ge=1)
    page_size: int = Field(10, description="每页数量", ge=1, le=100)
    type: str | None = Field(None, description="字典类型")

class DictItemQuery(BaseModel):
    """字典项查询参数"""
    page: int = Field(1, description="页码", ge=1)
    page_size: int = Field(10, description="每页数量", ge=1, le=100)

class DictItemBase(BaseModel):
    """字典项基础模型"""
    dict_id: int = Field(..., description="字典ID")
    name: str = Field(..., description="字典项名称", max_length=50)
    key: str = Field(..., description="字典项key", max_length=50)
    value: str = Field(..., description="字典项value", max_length=50)
    type: str = Field(..., description="字典项类型", max_length=50)

    @field_validator('*')
    @classmethod
    def check_empty_string(cls, v, info):
        if isinstance(v, str) and not v.strip():
            raise ValueError(f"{info.field_name} cannot be empty")
        return v.strip()

    @field_validator('key')
    @classmethod
    def validate_key(cls, v):
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', v):
            raise ValueError('key只能包含字母、数字和下划线，且必须以字母开头')
        return v

    @field_validator('dict_id')
    @classmethod
    def validate_dict_id(cls, v):
        if v <= 0:
            raise ValueError('无效的字典ID')
        return v

class DictItemCreate(DictItemBase):
    """创建字典项请求模型"""
    pass

class DictItemUpdate(DictItemBase):
    """更新字典项请求模型"""
    pass

class DictItemResponse(BaseModel):
    """字典项响应模型"""
    id: int
    item_code: str
    dict_id: int
    name: str
    key: str
    value: str
    type: str
    status: int
    create_time: int
    last_time: int

    class Config:
        from_attributes = True

class DictResponse(BaseModel):
    """字典响应模型"""
    id: int
    code: str
    name: str
    key: str
    value: str
    type: str
    status: int
    create_time: int
    last_time: int
    items: List[DictItemResponse] = []

    class Config:
        from_attributes = True

class DictListResponse(BaseModel):
    """字典列表响应模型"""
    total: int = Field(..., description="总数")
    items: List[DictResponse] = Field(default=[], description="字典列表")