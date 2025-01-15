from pydantic import BaseModel, Field
from typing import List, Optional

class DictBase(BaseModel):
    """字典基础模型"""
    name: str = Field(..., description="字典名称")
    key: str = Field(..., description="字典key")
    value: str = Field(..., description="字典value")
    type: str = Field(..., description="字典类型")
    status: int = Field(0, description="状态 0正常 1停用")

class DictCreate(DictBase):
    """创建字典请求模型"""
    pass

class DictUpdate(DictBase):
    """更新字典请求模型"""
    pass

class DictItemBase(BaseModel):
    """字典项基础模型"""
    dict_id: int = Field(..., description="字典ID")
    name: str = Field(..., description="字典项名称")
    key: str = Field(..., description="字典项key")
    value: str = Field(..., description="字典项value")
    type: str = Field(..., description="字典项类型")
    status: int = Field(0, description="状态 0正常 1停用")

class DictItemCreate(DictItemBase):
    """创建字典项请求模型"""
    pass

class DictItemUpdate(DictItemBase):
    """更新字典项请求模型"""
    pass

class DictResponse(DictBase):
    """字典响应模型"""
    id: int
    code: str
    create_time: int
    last_time: int
    items: List["DictItemResponse"] = []

    class Config:
        orm_mode = True

class DictItemResponse(DictItemBase):
    """字典项响应模型"""
    id: int
    item_code: str
    create_time: int
    last_time: int

    class Config:
        orm_mode = True

# 解决循环引用
DictResponse.update_forward_refs(DictItemResponse=DictItemResponse)

class DictListResponse(BaseModel):
    """字典列表响应模型"""
    total: int = Field(..., description="总数")
    items: List[DictResponse] = Field(default=[], description="字典列表")

class DictItemListResponse(BaseModel):
    """字典项列表响应模型"""
    total: int = Field(..., description="总数")
    items: List[DictItemResponse] = Field(default=[], description="字典项列表")