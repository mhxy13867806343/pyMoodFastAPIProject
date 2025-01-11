import uuid

from fastapi import APIRouter, Depends, status, Header, Request, HTTPException, Body
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
from sqlalchemy import or_

from config.error_messages import USER_ERROR
from tool.dbConnectionConfig import sendBindEmail, getVerifyEmail, generate_random_code
from tool.getLogger import globalLogger
from tool.msg import Message
from config.error_code import ErrorCode
from tool.validationTools import ValidationError
from tool import token as createToken
from .model import UserAuth, UserInfo
from models.user.model import UserInputs, UserType, UserStatus, EmailStatus, UserLoginRecord, LoginType, UserSex
from tool.db import getDbSession
from tool.dbRedis import RedisDB
from config.api_descriptions import ApiDescriptions
from config.user_constants import UserIdentifier
from tool.param_validator import validate_params
from app.users.schemas import UserUpdateRequest, EmailBindRequest, EmailCodeRequest

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
        "login_type": user.login_type.value,
        "avatar": user.avatar,
        "is_registered": user.is_registered
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
        "create_time": user.create_time,
        "avatar": user.avatar,
        "is_registered": user.is_registered
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

async def verify_email_code(email: str, code: str) -> bool:
    """
    验证邮箱验证码
    """
    try:
        # 从 Redis 获取验证码
        stored_code = await getVerifyEmail(email)
        if not stored_code:
            return False
        return stored_code == code
    except Exception as e:
        globalLogger.exception(f"验证邮箱验证码失败: {str(e)}")
        return False

async def bind_user_email(db: Session, user_id: int, email: str) -> bool:
    """
    绑定用户邮箱
    """
    try:
        # 查找用户
        user = db.query(UserInputs).filter(UserInputs.id == user_id).first()
        if not user:
            return False
        
        # 检查邮箱是否已被其他用户使用
        existing_user = db.query(UserInputs).filter(
            UserInputs.email == email,
            UserInputs.id != user_id
        ).first()
        if existing_user:
            return False
        
        # 更新用户邮箱
        user.email = email
        user.last_time = int(time.time())
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        globalLogger.exception(f"绑定用户邮箱失败: {str(e)}")
        return False

async def send_verification_code(email: str) -> bool:
    """
    发送验证码到邮箱
    """
    try:
        # 生成验证码
        code = generate_random_code()
        # 保存验证码到 Redis
        await sendBindEmail(email, code)
        return True
    except Exception as e:
        globalLogger.exception(f"发送验证码失败: {str(e)}")
        return False

async def update_user_info(db: Session, request: UserUpdateRequest) -> Optional[Dict[str, Any]]:
    """
    更新用户信息
    """
    try:
        # 查找用户
        db_user = db.query(UserInputs).filter(UserInputs.uid == request.uid).first()
        if not db_user:
            return None

        # 更新用户信息
        if request.username is not None:
            db_user.username = request.username
        if request.email is not None:
            db_user.email = request.email
        if request.phone is not None:
            db_user.phone = request.phone
        if request.name is not None:
            db_user.name = request.name
        if request.sex is not None:
            db_user.sex = UserSex(request.sex)
        if request.location is not None:
            db_user.location = request.location
        if request.avatar is not None:
            db_user.avatar = request.avatar
        if request.is_registered is not None:
            db_user.is_registered = request.is_registered

        db_user.last_time = int(time.time())
        db.commit()
        db.refresh(db_user)
        
        # 返回更新后的用户信息
        return get_user_data(db_user, include_private=True)
    except Exception as e:
        db.rollback()
        globalLogger.exception(f"更新用户信息失败: {str(e)}")
        return None

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
                name=f"{'Admin' if user_type != UserType.NORMAL else 'User'}_{int(time.time())}",
                avatar="",
                is_registered=0
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
@validate_params('user_id')
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
@validate_params('uid')
async def update_user(
    request: UserUpdateRequest,
    current_user_id: int = Depends(lambda: createToken.parse_token(required=True)),
    db: Session = Depends(getDbSession)
):
    """
    更新用户信息
    - 需要登录
    - 只能更新自己的信息
    """
    # 验证用户是否在更新自己的信息
    if not current_user_id:
        return Message.error(message=USER_ERROR["NO_PERMISSION"])
    
    try:
        # 更新用户信息
        user = await update_user_info(db, request)
        if not user:
            return Message.error(
                code=ErrorCode.NOT_FOUND.value,
                message=USER_ERROR["USER_NOT_FOUND"]
            )
        return Message.success(data=user)
    except Exception as e:
        globalLogger.exception(f"{USER_ERROR['UPDATE_FAILED']}: {str(e)}")
        return Message.error(
            code=ErrorCode.INTERNAL_ERROR.value,
            message=USER_ERROR["UPDATE_FAILED"]
        )

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
        # 清除用户缓存
        redis = RedisDB()
        await redis.delete(f"user:{current_user_id}")
        return Message.success()
    except Exception as e:
        globalLogger.exception(f"用户登出失败: {str(e)}")
        return Message.error(
            code=ErrorCode.INTERNAL_ERROR.value,
            message=USER_ERROR["LOGOUT_FAILED"]
        )

@userApp.post(
    "/email/bind",
    response_model=Message[Dict[str, Any]],
    summary="绑定邮箱"
)
async def bind_email(
    request: EmailBindRequest,
    current_user_id: int = Depends(lambda: createToken.parse_token(required=True)),
    db: Session = Depends(getDbSession)
):
    """
    绑定邮箱
    - 需要登录
    - 需要验证码
    """
    try:
        # 验证验证码
        if not await verify_email_code(request.email, request.code):
            return Message.error(
                code=ErrorCode.INVALID_PARAMS.value,
                message=USER_ERROR["INVALID_CODE"]
            )
        
        # 绑定邮箱
        success = await bind_user_email(db, current_user_id, request.email)
        if not success:
            return Message.error(
                code=ErrorCode.INTERNAL_ERROR.value,
                message=USER_ERROR["BIND_EMAIL_FAILED"]
            )
        return Message.success()
    except Exception as e:
        globalLogger.exception(f"{USER_ERROR['BIND_EMAIL_FAILED']}: {str(e)}")
        return Message.error(
            code=ErrorCode.INTERNAL_ERROR.value,
            message=USER_ERROR["BIND_EMAIL_FAILED"]
        )

@userApp.post(
    "/email/code",
    response_model=Message[Dict[str, Any]],
    summary="发送邮箱验证码"
)
async def send_email_code(
    request: EmailCodeRequest,
    current_user_id: int = Depends(lambda: createToken.parse_token(required=True))
):
    """
    发送邮箱验证码
    - 需要登录
    """
    try:
        # 发送验证码
        success = await send_verification_code(request.email)
        if not success:
            return Message.error(
                code=ErrorCode.INTERNAL_ERROR.value,
                message=USER_ERROR["SEND_CODE_FAILED"]
            )
        return Message.success()
    except Exception as e:
        globalLogger.exception(f"{USER_ERROR['SEND_CODE_FAILED']}: {str(e)}")
        return Message.error(
            code=ErrorCode.INTERNAL_ERROR.value,
            message=USER_ERROR["SEND_CODE_FAILED"]
        )
