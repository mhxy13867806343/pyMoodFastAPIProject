from pydantic import BaseModel, Field, field_validator
from typing import List, ForwardRef, Optional
import re

from tool.dbEnum import DictStatus


class DictBaseStatus(BaseModel):
    status: Optional[int] = Field(DictStatus.ALL, description="字典状态")
class DictBase(DictBaseStatus):
    """字典基础模型"""
    name: Optional[str] = Field(None, description="字典名称", max_length=50)
    key: Optional[str] = Field(None, description="字典key", max_length=50)
    value: Optional[str] = Field(None, description="字典value", max_length=50)
    type: Optional[str] = Field("0", description="字典类型", max_length=50)  # 默认为 "0"
    @field_validator('*')
    @classmethod
    def check_empty_string(cls, v, info):
        if isinstance(v, str):
            if not v.strip():
                raise ValueError(f"{info.field_name} cannot be empty")
            return v.strip()
        return v

    @field_validator('key')
    @classmethod
    def validate_key(cls, v):
        if v is not None:
            if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', v):
                raise ValueError('key只能包含字母、数字和下划线，且必须以字母开头')
        return v

#查询 列表 和分页
class DictBaseListMore(DictBase):
    page: int = Field(1, description="页码", gt=0)
    page_size: int = Field(10, description="每页数量", gt=0)

class DictCreate(DictBase):
    #新增
    pass
class DictBaseModelCodes(BaseModel):
    """字典基础模型"""
    code: str = Field(..., description="字典code", max_length=50)
class DictBaseCode(DictBase,DictBaseModelCodes):
    """字典基础模型"""
    pass
class DictBaseModelCode(DictBaseModelCodes,DictBaseStatus):
   pass
class DictBaseModelItem(DictBase):
    """字典基础模型"""
    dict_id:int= Field(..., description="字典id")