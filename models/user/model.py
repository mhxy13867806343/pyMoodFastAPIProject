from sqlalchemy import Column,Integer,String,ForeignKey
from sqlalchemy.orm import relationship
from extend.db import Base,LOCSESSION,ENGIN

import time
class AccountInputs(Base): # 用户信息
    __tablename__ = 'account'
    id = Column(Integer, primary_key=True, autoincrement=True)
    account = Column(String(100), nullable=False, default='')
    password = Column(String(100), nullable=False, default='')
    type = Column(Integer, nullable=False, default=0)
    create_time = Column(Integer, nullable=False, default=lambda: int(time.time()))
    last_time = Column(Integer, nullable=False, default=lambda: int(time.time()))
    email = Column(String(100), nullable=False, default='')
    name=Column(String(30),nullable=False,default='管理员')
    emailStatus = Column(Integer, nullable=False, default=0) #0未绑定 1已绑定
    status = Column(Integer, nullable=False, default=0) # 0:正常 1:禁用
    sex = Column(Integer, nullable=False, default=0) #11:男 12:女 0:未知
    signatures = relationship("Signature", back_populates="user", order_by="Signature.created_time")
    def __repr__(self):
        return f'<AccountInputs {self.account}>'


class Signature(Base):
    __tablename__ = 'signature'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('account.id'), nullable=False)
    content = Column(String(64), nullable=False)
    created_time = Column(Integer, nullable=False, default=lambda: int(time.time()))
    last_time = Column(Integer, nullable=False, default=lambda: int(time.time()))
    user = relationship("AccountInputs", back_populates="signatures")
    def __repr__(self):
        return f"<Signature(id={self.id}, user_id={self.user_id}, content='{self.content}', created_time={self.created_time}, last_time={self.last_time})>"