from sqlalchemy import Column, Integer, String, ForeignKey, Enum as SQLAlchemyEnum, Date, Index, BigInteger
from sqlalchemy.orm import relationship
import time
from tool.dbEnum import generate_uid, UserType, generate_default_name, EmailStatus, UserStatus, UserSex, LoginType
from datetime import date
from extend.db import Base

class UserInputs(Base): # 用户信息
    __tablename__ = 'user_inputs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    uid = Column(String(28), nullable=False, unique=True, default=generate_uid)
    username = Column(String(50), unique=True, nullable=True, comment='用户名，可用于登录')
    email = Column(String(100), nullable=True, default=None)
    password = Column(String(100), nullable=False, default=None)
    type = Column(SQLAlchemyEnum(UserType), nullable=False, default=UserType.NORMAL)
    login_type = Column(SQLAlchemyEnum(LoginType), nullable=False, default=LoginType.EMAIL, comment='登录方式')
    create_time = Column(Integer, nullable=False, default=lambda: int(time.time()))
    last_time = Column(Integer, nullable=False, default=lambda: int(time.time()))
    name = Column(String(30), nullable=False, default=generate_default_name)
    phone = Column(String(11), nullable=False, default="")
    emailCode = Column(SQLAlchemyEnum(EmailStatus), nullable=False, default=EmailStatus.UNBOUND)
    avatar = Column(String(255), nullable=False, default="", comment="用户头像")
    is_registered = Column(Integer, nullable=False, default=0, comment="注册状态：0=未注册完成，1=注册成功")
    status = Column(SQLAlchemyEnum(UserStatus), nullable=False, default=UserStatus.NORMAL)
    sex = Column(SQLAlchemyEnum(UserSex), nullable=False, default=UserSex.UNKNOWN)
    location=Column(String(30), nullable=False, default="ip地址")
    signature=Column(String(32),nullable=False,default="") #签名

    # 与登录记录表的关系，使用 lazy='dynamic' 实现延迟加载
    login_records = relationship("UserLoginRecord", back_populates="user", lazy='dynamic')

    # 创建联合索引
    __table_args__ = (
        Index('ix_user_inputs_email_login_type', 'email', 'login_type'),
        Index('ix_user_inputs_username_login_type', 'username', 'login_type'),
    )


class UserLoginRecord(Base):
    """用户登录记录表"""
    __tablename__ = 'user_login_record'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_uid = Column(String(28), ForeignKey('user_inputs.uid'), nullable=False, comment='用户UID')
    login_date = Column(Date, nullable=False, comment='登录日期')
    login_time = Column(Integer, nullable=False, comment='登录时间戳')
    continuous_days = Column(Integer, default=1, comment='连续登录天数')
    create_time = Column(Integer, nullable=False, default=lambda: int(time.time()))
    last_time = Column(Integer, nullable=False, default=lambda: int(time.time()))
    
    # 与用户表的关系
    user = relationship("UserInputs", back_populates="login_records", foreign_keys=[user_uid])

    def __init__(self, user_uid: str, login_date: date, login_time: int, continuous_days: int = 1):
        self.user_uid = user_uid
        self.login_date = login_date
        self.login_time = login_time
        self.continuous_days = continuous_days
