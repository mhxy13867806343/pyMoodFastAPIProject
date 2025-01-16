from sqlalchemy import Column, Integer, String, ForeignKey, Enum as SQLAlchemyEnum, Date, Index, BigInteger
from sqlalchemy.orm import relationship
import time
from datetime import date
from extend.db import Base
from tool.dbEnum import DictStatus


class SYSDict(Base):
    __tablename__ = 'sys_dict'
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    #code由系统生成，不可修改
    code=Column(String(50), nullable=False, unique=True,default="", comment="字典code")
    name = Column(String(50), nullable=False, unique=True ,default="", comment="字典名称")
    key = Column(String(50), nullable=False, unique=True, default="", comment="字典key")
    value = Column(String(50), nullable=False, default="", comment="字典value")
    type = Column(String(50), nullable=False, default="0", comment="字典类型")
    status = Column(Integer, nullable=False, default=0, comment="状态 0 正常 1 停用")
    create_time = Column(Integer, nullable=False, default=lambda: int(time.time()), comment="创建时间")
    last_time = Column(Integer, nullable=False, default=lambda: int(time.time()), onupdate=lambda: int(time.time()), comment="更新时间")
    # 一个字典可以有多个字典项，通过 parent_code 关联
    items = relationship("SYSDictItem", backref="dict", lazy="dynamic", foreign_keys="[SYSDictItem.parent_code]")

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "key": self.key,
            "value": self.value,
            "type": self.type,
            "status": self.status,
            "create_time": self.create_time,
            "last_time": self.last_time
        }

#某个字典下面的多字典项
class SYSDictItem(Base):
    __tablename__ = 'sys_dict_item'
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    #code由系统生成，不可修改
    item_code=Column(String(50), nullable=False, unique=True,default="", comment="字典项code")
    #外键关联字典表
    parent_code = Column(String(50), ForeignKey('sys_dict.code'), nullable=False, comment="父字典code")
    name = Column(String(50), nullable=False, unique=True ,default="", comment="字典项名称")
    key = Column(String(50), nullable=False, unique=True, default="", comment="字典项key")
    value = Column(String(50), nullable=False, default="", comment="字典项value")
    type = Column(String(50), nullable=False, default="0", comment="字典项类型")
    status = Column(Integer, nullable=False, default=0, comment="状态 0 正常 1 停用")
    create_time = Column(Integer, nullable=False, default=lambda: int(time.time()), comment="创建时间")
    last_time = Column(Integer, nullable=False, default=lambda: int(time.time()), onupdate=lambda: int(time.time()), comment="更新时间")

    def to_dict(self):
        """转换为字典"""
        dict_obj = self.dict  # 获取关联的字典对象
        return {
            "id": self.id,
            "item_code": self.item_code,
            "code": dict_obj.code if dict_obj else None,  # 从关联的字典对象获取code
            "name": self.name,
            "key": self.key,
            "value": self.value,
            "type": self.type,
            "status": self.status,
            "create_time": self.create_time,
            "last_time": self.last_time
        }