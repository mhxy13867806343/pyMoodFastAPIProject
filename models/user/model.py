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
    logout_records = relationship("UserLogoutRecords", back_populates="user", lazy='dynamic')
    next_lv = relationship("UserLvNext", back_populates="user", lazy='dynamic')

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
    userLogout = relationship("UserInputs", back_populates="login_records", foreign_keys=[user_uid])

    def __init__(self, user_uid: str, login_date: date, login_time: int, continuous_days: int = 1):
        self.user_uid = user_uid
        self.login_date = login_date
        self.login_time = login_time
        self.continuous_days = continuous_days


class UserLogoutRecords(Base):
    """用户登出记录表"""
    __tablename__ = 'user_logout_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_uid = Column(String(28), ForeignKey('user_inputs.uid'), nullable=False, comment='用户UID')
    logout_time = Column(BigInteger, nullable=False, comment='登出时间戳')
    logout_date = Column(Date, nullable=False, comment='登出日期')
    create_time = Column(Integer, nullable=False, default=lambda: int(time.time()))
    last_time = Column(Integer, nullable=False, default=lambda: int(time.time()))
    
    # 与用户表的关系
    user = relationship("UserInputs", back_populates="logout_records", foreign_keys=[user_uid])

    def __init__(self, user_uid: str, logout_date: date, logout_time: int):
        self.user_uid = user_uid
        self.logout_date = logout_date
        self.logout_time = logout_time
        self.create_time = int(time.time())
        self.last_time = int(time.time())


class UserLvNext(Base):
    """用户等级表"""
    __tablename__ = 'user_lv_next'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_uid = Column(String(28), ForeignKey('user_inputs.uid'), nullable=False, comment='用户UID')
    lv = Column(Integer, nullable=False, default=0, comment='用户等级')
    max_lv = Column(Integer, nullable=False, default=10, comment='最大等级')
    exp = Column(Integer, nullable=False, default=0, comment='当前经验值')
    next_lv = Column(Integer, nullable=False, default=0, comment='下一级所需积分')
    create_time = Column(Integer, nullable=False, default=lambda: int(time.time()), comment='创建时间')
    last_time = Column(Integer, nullable=False, default=lambda: int(time.time()), comment='最后更新时间')

    # 与用户表的关系
    user = relationship("UserInputs", back_populates="user_lv_next", foreign_keys=[user_uid])

    def __init__(self, user_uid: str):
        self.user_uid = user_uid
        self.create_time = int(time.time())
        self.last_time = int(time.time())

    def get_level_by_exp(self, total_exp: int, max_lv: int = 10, base_exp: int = 100, growth_factor: float = 1.5) -> dict:
        """
        根据总经验值计算当前等级和升级所需经验
        
        参数：
        - total_exp: 当前总经验值
        - max_lv: 最大等级
        - base_exp: 基础经验值
        - growth_factor: 经验值增长系数
        
        返回：包含当前等级、当前等级经验、下一级所需总经验的字典
        """
        lv_list = self.lv_sum(max_lv, base_exp, growth_factor)
        
        for i, level_info in enumerate(lv_list):
            if total_exp < level_info['exp']:
                current_lv = i - 1
                current_lv_exp = lv_list[current_lv]['exp']
                next_lv_total_exp = level_info['exp']
                
                return {
                    'current_lv': current_lv,
                    'current_lv_exp': current_lv_exp,
                    'next_lv_total_exp': next_lv_total_exp,
                    'exp_to_next_lv': next_lv_total_exp - total_exp
                }
        
        # 如果经验值超过最大等级
        return {
            'current_lv': max_lv,
            'current_lv_exp': lv_list[-1]['exp'],
            'next_lv_total_exp': None,
            'exp_to_next_lv': 0
        }

    def update_exp(self, exp_gained: int) -> dict:
        """更新经验值并检查是否升级"""
        self.exp += exp_gained
        self.last_time = int(time.time())
        level_info = self.get_level_by_exp(self.exp)
        self.lv = level_info['current_lv']
        self.next_lv = level_info['next_lv_total_exp']
        return level_info

    def can_level_up(self) -> bool:
        """
        检查是否可以升级
        
        :return: 是否可以升级
        """
        level_info = self.get_level_by_exp(self.exp)
        return level_info['current_lv'] > self.lv

    def get_exp_table(self) -> list[dict]:
        """
        获取等级经验对照表
        :return: 等级经验列表
        """
        lv_list = self.lv_sum()
        exp_table = []
        
        for i in range(len(lv_list)):
            current = lv_list[i]
            next_exp = lv_list[i + 1]['exp'] if i < len(lv_list) - 1 else None
            
            exp_table.append({
                "等级": current['lv'],
                "当前等级累计经验": current['exp'],
                "升级所需经验": next_exp - current['exp'] if next_exp else 0,
                "下级累计经验": next_exp
            })
        
        return exp_table

    def get_login_days_exp(self, total_days: int, current_month: int) -> dict:
        """
        根据登录天数获取额外经验值，每月重置
        :param total_days: 本月的登录天数
        :param current_month: 当前月份
        :return: 奖励信息
        """
        # 确保天数在1-31之间
        total_days = max(1, min(total_days, 31))
        
        # 定义奖励节点
        exp_rewards = {
            7: 7,   # 7天奖励7点
            15: 15, # 15天奖励15点
            22: 22, # 22天奖励22点
            30: 30  # 30天奖励30点
        }
        
        # 获取当前用户经验值
        current_exp = self.exp
        reward_exp = 0
        reward_type = None
        
        # 找到最接近但不超过当前天数的奖励
        for days, exp in exp_rewards.items():
            if total_days == days:  # 只在刚好达到天数时给予奖励
                reward_exp = exp
                reward_type = f"{days}天登录奖励"
                break
        
        # 计算新的总经验值
        new_total_exp = current_exp + reward_exp
        
        return {
            'current_exp': current_exp,      # 当前经验值
            'reward_exp': reward_exp,        # 奖励经验值
            'new_total_exp': new_total_exp,  # 新的总经验值
            'reward_type': reward_type,      # 奖励类型
            'login_days': total_days,        # 登录天数
            'current_month': current_month   # 当前月份
        }

    def update_exp_with_login(self, total_days: int, current_month: int):
        """
        更新经验值（包含登录天数奖励）
        :param total_days: 本月的登录天数
        :param current_month: 当前月份
        :return: 经验值更新信息
        """
        # 获取登录奖励信息
        reward_info = self.get_login_days_exp(total_days, current_month)
        
        if reward_info['reward_exp'] > 0:
            # 只有在有奖励时才更新经验值
            self.exp = reward_info['new_total_exp']
            
            # 检查是否需要升级
            level_info = self.get_level_by_exp(self.exp)
            if level_info['current_lv'] > self.lv:
                self.lv = level_info['current_lv']
                self.next_lv = level_info['next_lv_total_exp']
        
        return {
            'exp_before': reward_info['current_exp'],
            'exp_gained': reward_info['reward_exp'],
            'total_exp': reward_info['new_total_exp'],
            'current_level': self.lv,
            'next_level_exp': self.next_lv,
            'login_days': reward_info['login_days'],
            'current_month': reward_info['current_month'],
            'reward_type': reward_info['reward_type']
        }
