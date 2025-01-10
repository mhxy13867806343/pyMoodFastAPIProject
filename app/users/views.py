from fastapi import APIRouter, Depends, status, Header, Request
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
import time
import random
import string
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta, date
import re
from typing import Optional, Dict, Any

from config.error_messages import USER_ERROR
from tool.dbConnectionConfig import sendBindEmail, getVerifyEmail, generate_random_code
from tool.msg import Message
from config.error_code import ErrorCode
from tool.validationTools import ValidationError
from .model import UserAuth, UserInfo
from tool.db import getDbSession
from tool import token as createToken
from models.user.model import UserInputs, UserType, UserStatus, EmailStatus, UserLoginRecord, LoginType, UserLogoutRecord
from tool.dbRedis import RedisDB
from config.api_descriptions import ApiDescriptions
from config.user_constants import UserIdentifier

# 加载环境变量
load_dotenv()
EXPIRE_TIME = int(os.getenv('EXPIRE_TIME', str(60*60*24*30)))  # 默认30天

redis_db = RedisDB()
userApp = APIRouter(tags=["用户相关"])

# 管理员账号配置
ADMIN_ACCOUNTS = {
    # 用户名登录的管理员
    'admin': {'type': UserType.ADMIN, 'login_type': LoginType.USERNAME},
    'superadmin': {'type': UserType.SUPER, 'login_type': LoginType.USERNAME},
    # 邮箱登录的管理员
    'admin@example.com': {'type': UserType.ADMIN, 'login_type': LoginType.EMAIL},
    'super@example.com': {'type': UserType.SUPER, 'login_type': LoginType.EMAIL}
}

def is_valid_email(email: str) -> bool:
    """验证邮箱格式"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def handle_login_record(db: Session, user_id: int, current_time: int) -> int:
    """处理登录记录，返回连续登录天数"""
    today = date.today()
    
    # 获取最后一次登录记录
    last_record = db.query(UserLoginRecord).filter(
        UserLoginRecord.user_id == user_id
    ).order_by(UserLoginRecord.login_date.desc()).first()

    continuous_days = 1  # 默认为1天
    if last_record:
        days_diff = (today - last_record.login_date).days
        if days_diff == 1:  # 连续登录
            continuous_days = last_record.continuous_days + 1
        elif days_diff == 0:  # 今天已经登录过
            continuous_days = last_record.continuous_days
        else:  # 断签，重置为1天
            continuous_days = 1
    
    # 创建新的登录记录
    login_record = UserLoginRecord(
        user_id=user_id,
        login_date=today,
        login_time=current_time,
        create_time=current_time,
        last_time=current_time,
        continuous_days=continuous_days
    )
    db.add(login_record)
    
    return continuous_days

def prepare_user_data(
    user: UserInputs, 
    token: Optional[str] = None, 
    continuous_days: int = 1,
    include_password: bool = False
) -> Dict[str, Any]:
    """
    准备用户数据
    :param user: 用户对象
    :param token: 用户token
    :param continuous_days: 连续登录天数
    :param include_password: 是否包含密码（用于缓存）
    :return: 用户数据字典
    """
    data = {
        "id": user.id,
        "uid": user.uid,
        "username": user.username,
        "email": user.email,
        "name": user.name,
        "phone": user.phone,
        "location": user.location,
        "sex": user.sex.value,
        "type": user.type.value,
        "status": user.status.value,
        "emailCode": user.emailCode.value,
        "create_time": user.create_time,
        "last_time": user.last_time,
        "continuous_days": continuous_days,
        "login_type": user.login_type.value
    }
    
    if token:
        data["token"] = token
        
    if include_password:
        data["password"] = user.password
        
    return data

def get_user_data(user: UserInputs, include_private: bool = False) -> Dict[str, Any]:
    """
    获取用户数据
    :param user: 用户对象
    :param include_private: 是否包含私密信息
    :return: 用户数据字典
    """
    # 基本公开信息
    data = {
        "id": user.id,
        "uid": user.uid,
        "name": user.name,
        "sex": user.sex.value,
        "type": user.type.value,
        "create_time": user.create_time
    }

    # 包含私密信息
    if include_private:
        data.update({
            "username": user.username,
            "email": user.email,
            "phone": user.phone,
            "location": user.location,
            "status": user.status.value,
            "emailCode": user.emailCode.value,
            "last_time": user.last_time,
        })

    return data

@userApp.post(
    "/auth",
    response_model=Message[Dict[str, Any]],
    summary=ApiDescriptions.AUTH.summary
)
async def auth(user_auth: UserAuth, db: Session = Depends(getDbSession)):
    """
    用户认证接口：处理注册和登录
    - 优先从 Redis 缓存获取用户信息
    - 支持邮箱和用户名两种登录方式
    - 如果用户不存在，则注册新用户并自动登录
    - 如果用户存在，则验证密码进行登录
    - 记录登录信息到 MySQL 和 Redis
    - 处理连续登录天数（断签重置为1天）
    - 特殊处理管理员账号
    """
    if not user_auth.account or not user_auth.password:
        return Message.error(code=ErrorCode.INVALID_PARAMS.value, message=USER_ERROR["ACCOUNT_NOT_EMAIL_FOUND"])
    try:
        current_time = int(time.time())
        
        # 1. 先从 Redis 缓存获取用户信息
        cached_user = redis_db.get_user_info(user_auth.account, user_auth.login_type)
        if cached_user:
            # 验证密码
            if not createToken.check_password(user_auth.password, cached_user["password"]):
                return Message.error(
                    message=USER_ERROR["ACCOUNT_OR_PASSWORD_ERROR"],
                    code=ErrorCode.ACCOUNT_OR_PASSWORD_ERROR.value
                )
            
            # 生成新的token
            token_expire = timedelta(seconds=EXPIRE_TIME * 2) if cached_user['type'] != UserType.NORMAL else timedelta(seconds=EXPIRE_TIME)
            token = createToken.create_token(
                {
                    "sub": str(cached_user["id"]),
                    "type": cached_user['type'],
                    "login_type": cached_user['login_type']
                }, 
                token_expire
            )
            
            # 更新缓存中的token
            cached_user["token"] = token
            cached_user["last_time"] = current_time
            
            # 获取登录记录
            login_record = redis_db.get_login_record(cached_user['id'])
            continuous_days = 1
            if login_record:
                last_login = datetime.strptime(login_record['last_login_date'], '%Y-%m-%d').date()
                days_diff = (date.today() - last_login).days
                if days_diff == 1:  # 连续登录
                    continuous_days = login_record['continuous_days'] + 1
                elif days_diff == 0:  # 今天已经登录过
                    continuous_days = login_record['continuous_days']
                else:  # 断签，重置为1天
                    continuous_days = 1
                    
            # 更新 Redis 登录记录
            redis_db.update_login_record(cached_user['id'], continuous_days)
            
            # 更新数据库登录记录
            handle_login_record(db, cached_user['id'], current_time)
            
            # 更新用户最后登录时间
            user = db.query(UserInputs).get(cached_user['id'])
            if user:
                user.last_time = current_time
                db.commit()
            
            # 准备用户数据（包含密码用于缓存）
            user_data = prepare_user_data(user, token, continuous_days, include_password=True)
            
            # 更新缓存
            redis_db.cache_user_info(user_data)
            
            # 删除敏感信息
            response_data = user_data.copy()
            del response_data['password']
            return Message.success(
                message=Message.success()["msg"],
                data=response_data
            )
        
        # 2. 如果缓存中没有，从数据库查询
        query = db.query(UserInputs)
        if user_auth.login_type == LoginType.EMAIL:
            if not is_valid_email(user_auth.account):
                return Message.error(message=USER_ERROR["EMAIL_INVALID_FORMAT"])
            existing_user = query.filter(
                UserInputs.email == user_auth.account,
                UserInputs.login_type == LoginType.EMAIL
            ).first()
        else:
            existing_user = query.filter(
                UserInputs.username == user_auth.account,
                UserInputs.login_type == LoginType.USERNAME
            ).first()

        if existing_user is None:
            # 注册新用户
            hashed_password = createToken.getHashPwd(user_auth.password)
            
            # 检查是否是管理员账号
            admin_info = ADMIN_ACCOUNTS.get(user_auth.account)
            if admin_info and admin_info['login_type'] == user_auth.login_type:
                user_type = admin_info['type']
                login_type = admin_info['login_type']
            else:
                user_type = UserType.NORMAL
                login_type = user_auth.login_type
            
            new_user = UserInputs(
                email=user_auth.account if login_type == LoginType.EMAIL else None,
                username=user_auth.account if login_type == LoginType.USERNAME else None,
                password=hashed_password,
                create_time=current_time,
                last_time=current_time,
                type=user_type,
                login_type=login_type,
                status=UserStatus.NORMAL,
                name=f"{'Admin' if user_type != UserType.NORMAL else 'User'}_{int(time.time())}"
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            existing_user = new_user

        else:
            # 登录验证
            if not createToken.check_password(user_auth.password, existing_user.password):
                return Message.error(message=USER_ERROR["ACCOUNT_OR_PASSWORD_ERROR"], code=ErrorCode.ACCOUNT_OR_PASSWORD_ERROR.value)
            if existing_user.status == UserStatus.DISABLED:
                return Message.error(message=USER_ERROR["ACCOUNT_DISABLED"])
            
            # 检查是否需要更新用户类型（比如普通用户被加入管理员白名单）
            admin_info = ADMIN_ACCOUNTS.get(user_auth.account)
            if admin_info and admin_info['login_type'] == existing_user.login_type and existing_user.type != admin_info['type']:
                existing_user.type = admin_info['type']
                db.commit()

        # 处理登录记录并获取连续登录天数
        continuous_days = handle_login_record(db, existing_user.id, current_time)
        
        # 更新用户最后登录时间
        existing_user.last_time = current_time
        db.commit()

        # 生成token，管理员token有效期更长
        token_expire = timedelta(seconds=EXPIRE_TIME * 2) if existing_user.type != UserType.NORMAL else timedelta(seconds=EXPIRE_TIME)
        token = createToken.create_token(
            {
                "sub": str(existing_user.id),
                "type": int(existing_user.type),
                "login_type": int(existing_user.login_type)
            }, 
            token_expire
        )
        
        # 准备用户数据（包含密码用于缓存）
        user_data = prepare_user_data(existing_user, token, continuous_days, include_password=True)
        
        # 更新 Redis 缓存
        redis_db.cache_user_info(user_data)
        redis_db.update_login_record(existing_user.id, continuous_days)
        
        # 删除敏感信息
        response_data = user_data.copy()
        del response_data['password']
        
        return Message.success(
            message=Message.success()["msg"], 
            data=response_data
        )

    except SQLAlchemyError as e:
        db.rollback()
        return Message.server_error()

@userApp.get(
    "/info",
    response_model=Message[Dict[str, Any]],
    summary="获取当前登录用户信息"
)
async def get_current_user_info(
    current_user_id: int = Depends(lambda: createToken.parse_token(required=True)),
    db: Session = Depends(getDbSession)
):
    """
    获取当前登录用户的详细信息
    - 从 token 中获取用户 ID
    - 返回用户的所有可见信息
    """
    try:
        # 查找用户
        current_user = db.query(UserInputs).filter(UserInputs.id == current_user_id).first()
        if not current_user:
            return Message.error(
                code=ErrorCode.USER_NOT_FOUND.value,
                message=USER_ERROR["USER_NOT_FOUND"]
            )

        # 获取用户的连续登录天数
        login_record = db.query(UserLoginRecord).filter(
            UserLoginRecord.user_id == current_user_id
        ).order_by(UserLoginRecord.login_date.desc()).first()
        
        # 获取用户数据（包含私密信息）
        user_data = get_user_data(current_user, include_private=True)
        user_data["continuous_days"] = login_record.continuous_days if login_record else 1

        return Message.success(data=user_data)
    except Exception as e:
        return Message.server_error()

@userApp.get(
    "/info/{user_id}",
    response_model=Message[Dict[str, Any]],
    summary="获取指定用户的公开信息"
)
async def get_user_info(
    user_id: int,
    current_user_id: Optional[int] = Depends(lambda: createToken.parse_token(required=False)),
    db: Session = Depends(getDbSession)
):
    """
    获取指定用户的公开信息
    - 如果是获取自己的信息，返回所有信息
    - 如果是获取其他用户的信息，只返回公开信息
    - 如果未登录，只返回最基本的公开信息
    """
    try:
        # 查找目标用户
        target_user = db.query(UserInputs).filter(UserInputs.id == user_id).first()
        if not target_user:
            return Message.error(
                code=ErrorCode.USER_NOT_FOUND.value,
                message=USER_ERROR["USER_NOT_FOUND"]
            )

        # 判断是否是查看自己的信息
        is_self = current_user_id and current_user_id == user_id
        user_data = get_user_data(target_user, include_private=is_self)

        # 如果是查看自己的信息，添加连续登录天数
        if is_self:
            login_record = db.query(UserLoginRecord).filter(
                UserLoginRecord.user_id == user_id
            ).order_by(UserLoginRecord.login_date.desc()).first()
            user_data["continuous_days"] = login_record.continuous_days if login_record else 1

        return Message.success(data=user_data)
    except Exception as e:
        return Message.server_error()

@userApp.put(
    "/update",
    response_model=Message[Dict[str, Any]],
    summary="更新用户信息"
)
async def update_user_info(
    user_info: UserInfo,
    current_user_id: int = Depends(lambda: createToken.parse_token(required=True)),
    db: Session = Depends(getDbSession)
):
    """
    更新用户信息
    - 需要登录
    - 只能更新自己的信息
    """
    try:
        # 查找用户
        current_user = db.query(UserInputs).filter(UserInputs.id == current_user_id).first()
        if not current_user:
            return Message.error(
                code=ErrorCode.USER_NOT_FOUND.value,
                message=USER_ERROR["USER_NOT_FOUND"]
            )

        # 更新用户信息
        if user_info.name is not None:
            current_user.name = user_info.name
        if user_info.phone is not None:
            current_user.phone = user_info.phone
        if user_info.location is not None:
            current_user.location = user_info.location
        if user_info.sex is not None:
            current_user.sex = user_info.sex
        
        current_user.last_time = int(time.time())
        
        # 同步更新 Redis 缓存
        if current_user.email:
            redis_db.delete_user_info(current_user.email, LoginType.EMAIL)
        if current_user.username:
            redis_db.delete_user_info(current_user.username, LoginType.USERNAME)
        
        db.commit()
        
        return Message.success(
            data={
                "user_id": current_user_id,
                "update_time": current_user.last_time
            }
        )
    except ValidationError as ve:
        db.rollback()
        return Message.error(message=str(ve))
    except Exception as e:
        db.rollback()
        return Message.server_error()

@userApp.post(
    "/logout",
    response_model=Message[Dict[str, Any]],
    summary="用户登出"
)
async def logout(
    current_user_id: int = Depends(lambda: createToken.parse_token(required=True)),
    db: Session = Depends(getDbSession)
):
    """
    用户登出
    - 需要登录
    - 清除缓存
    """
    try:
        # 查找用户
        current_user = db.query(UserInputs).filter(UserInputs.id == current_user_id).first()
        if not current_user:
            return Message.error(
                code=ErrorCode.USER_NOT_FOUND.value,
                message=USER_ERROR["USER_NOT_FOUND"]
            )

        current_time = int(time.time())

        # 更新用户最后登出时间
        current_user.last_time = current_time
        
        # 创建登出记录
        logout_record = UserLogoutRecord(
            user_id=current_user_id,
            logout_time=current_time,
            create_time=current_time
        )
        db.add(logout_record)
        
        # 清除Redis缓存
        redis_db.delete_user_info(current_user.email, LoginType.EMAIL)
        if current_user.username:
            redis_db.delete_user_info(current_user.username, LoginType.USERNAME)
            
        db.commit()
        
        return Message.success(
            data={
                "user_id": current_user_id,
                "logout_time": current_time
            }
        )
    except SQLAlchemyError as e:
        db.rollback()
        return Message.server_error()
    except Exception as e:
        return Message.server_error()

@userApp.post(
    "/email/bind",
    response_model=Message[Dict[str, Any]],
    summary="绑定邮箱"
)
async def bind_email(
    email: str,
    code: str,
    current_user_id: int = Depends(lambda: createToken.parse_token(required=True)),
    db: Session = Depends(getDbSession)
):
    """
    绑定邮箱
    - 需要登录
    - 需要验证码
    """
    try:
        # 验证邮箱格式
        if not is_valid_email(email):
            return Message.error(
                message=USER_ERROR["EMAIL_INVALID_FORMAT"]
            )

        # 验证验证码
        redis_key = f"email_verify_{email}"
        stored_code = redis_db.get(redis_key)
        if not stored_code or stored_code != code:
            return Message.error(
                message=USER_ERROR["EMAIL_CODE_INVALID"]
            )

        # 查找用户
        current_user = db.query(UserInputs).filter(UserInputs.id == current_user_id).first()
        if not current_user:
            return Message.error(
                code=ErrorCode.USER_NOT_FOUND.value,
                message=USER_ERROR["USER_NOT_FOUND"]
            )

        # 检查邮箱是否已被其他用户使用
        existing_user = db.query(UserInputs).filter(
            UserInputs.email == email,
            UserInputs.id != current_user_id
        ).first()
        if existing_user:
            return Message.error(
                message=USER_ERROR["EMAIL_ALREADY_BOUND"]
            )

        # 更新用户邮箱
        current_user.email = email
        current_user.emailCode = EmailStatus.BOUND
        current_user.last_time = int(time.time())
        
        # 清除旧的缓存
        if current_user.email:
            redis_db.delete_user_info(current_user.email, LoginType.EMAIL)
        if current_user.username:
            redis_db.delete_user_info(current_user.username, LoginType.USERNAME)
        
        db.commit()
        
        return Message.success(
            data={
                "user_id": current_user_id,
                "email": email,
                "bind_time": current_user.last_time
            }
        )
    except Exception as e:
        db.rollback()
        return Message.server_error()

@userApp.post(
    "/email/code",
    response_model=Message[Dict[str, Any]],
    summary="发送邮箱验证码"
)
async def send_email_code(
    email: str,
    current_user_id: int = Depends(lambda: createToken.parse_token(required=True)),
    db: Session = Depends(getDbSession)
):
    """
    发送邮箱验证码
    - 需要登录
    """
    try:
        # 验证邮箱格式
        if not is_valid_email(email):
            return Message.error(
                message=USER_ERROR["EMAIL_INVALID_FORMAT"]
            )

        # 查找用户
        current_user = db.query(UserInputs).filter(UserInputs.id == current_user_id).first()
        if not current_user:
            return Message.error(
                code=ErrorCode.USER_NOT_FOUND.value,
                message=USER_ERROR["USER_NOT_FOUND"]
            )

        # 检查发送频率限制
        redis_key = f"email_verify_{email}"
        if redis_db.exists(redis_key):
            return Message.error(
                message=USER_ERROR["EMAIL_CODE_FREQ_LIMIT"]
            )

        # 生成并发送验证码
        verify_code = generate_random_code()
        if not sendBindEmail(email, verify_code):
            return Message.error(
                message=USER_ERROR["EMAIL_SEND_FAILED"]
            )

        # 存储验证码到 Redis，设置5分钟过期
        redis_db.setex(redis_key, 300, verify_code)
        
        return Message.success(
            data={
                "user_id": current_user_id,
                "email": email,
                "expire_time": 300
            }
        )
    except Exception as e:
        return Message.server_error()
