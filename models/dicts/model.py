from sqlalchemy import Column, Integer, String, ForeignKey, Enum as SQLAlchemyEnum, Date, Index, BigInteger
from sqlalchemy.orm import relationship
import time
from datetime import date
from extend.db import Base
from tool.dbEnum import UserStatus


class SYSDict(Base):
    __tablename__ = 'sys_dict'
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    #code由系统生成，不可修改
    code=Column(String(50), nullable=False, unique=True,default="", comment="字典code")
    name = Column(String(50), nullable=False, unique=True ,default="", comment="字典名称")
    key = Column(String(50), nullable=False, unique=True, default="", comment="字典key")
    value = Column(String(50), nullable=False, default="", comment="字典value")
    type = Column(String(50), nullable=False, default="", comment="字典类型")
    status = Column(Integer, nullable=False, default=UserStatus.NORMAL, comment="状态 0 正常 1 停用")
    create_time = Column(Integer, nullable=False, default=lambda: int(time.time()), comment="创建时间")
    last_time = Column(Integer, nullable=False, default=lambda: int(time.time()), onupdate=lambda: int(time.time()), comment="更新时间")
    items = relationship("SYSDictItem", backref="dict", lazy="dynamic")

#某个字典下面的多字典项
class SYSDictItem(Base):
    __tablename__ = 'sys_dict_item'
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    #code由系统生成，不可修改
    item_code=Column(String(50), nullable=False, unique=True,default="", comment="字典code")
    dict_id = Column(Integer, ForeignKey('sys_dict.id'), nullable=False, comment="字典id")
    name = Column(String(50), nullable=False, unique=True ,default="", comment="字典名称")
    key = Column(String(50), nullable=False, unique=True, default="", comment="字典key")
    value = Column(String(50), nullable=False, default="", comment="字典value")
    type = Column(String(50), nullable=False, default="", comment="字典类型")
    create_time = Column(Integer, nullable=False, default=lambda: int(time.time()), comment="创建时间")
    last_time = Column(Integer, nullable=False, default=lambda: int(time.time()), onupdate=lambda: int(time.time()), comment="更新时间")
    status = Column(Integer, nullable=False, default=UserStatus.NORMAL, comment="状态 0 正常 1 停用")
    