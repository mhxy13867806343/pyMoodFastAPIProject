from fastapi import APIRouter, Depends, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
import time
import random
import string
from datetime import datetime, timedelta, date
import re

from tool.dbConnectionConfig import sendBindEmail, getVerifyEmail, generate_random_code
from tool.msg import Message, MsgCode
from .model import UserAuth, UserInfo
from tool.db import getDbSession
from tool import token as createToken
from models.user.model import UserInputs, UserType, UserStatus, EmailStatus, UserLoginRecord, LoginType, UserLogoutRecord
from tool.classDb import HttpStatus
from tool.statusTool import EXPIRE_TIME
from tool.dbRedis import RedisDB
from config.api_descriptions import ApiDescriptions

redis_db = RedisDB()
userApp = APIRouter()

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

def prepare_user_data(user: UserInputs, token: str, continuous_days: int) -> dict:
    """准备用户数据，用于缓存和返回"""
    return {
        "id": user.id,
        "token": token,
        "uid": user.uid,
        "type": int(user.type),
        "email": user.email,
        "username": user.username,
        "password": user.password,  # 用于缓存中的密码验证
        "create_time": int(user.create_time),
        "last_time": int(user.last_time),
        "name": user.name,
        "status": int(user.status),
        "phone": user.phone,
        "emailCode": int(user.emailCode),
        "location": user.location,
        "sex": int(user.sex),
        "continuous_days": continuous_days,
        "is_admin": user.type in [UserType.ADMIN, UserType.SUPER],
        "is_super_admin": user.type == UserType.SUPER,
        "login_type": int(user.login_type)
    }

@userApp.post('/auth', description="用户认证", summary="用户注册或登录")
def auth(user_auth: UserAuth, db: Session = Depends(getDbSession)):
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
        return HttpStatus.error()

    try:
        current_time = int(time.time())
        
        # 1. 先从 Redis 缓存获取用户信息
        cached_user = redis_db.get_user_info(user_auth.account, user_auth.login_type)
        if cached_user:
            # 验证密码
            if not createToken.check_password(user_auth.password, cached_user['password']):
                return HttpStatus.error(message=Message.get(MsgCode.ACCOUNT_OR_PASSWORD_ERROR.value)["msg"])
            if int(cached_user['status']) == UserStatus.DISABLED:
                return HttpStatus.error(message=Message.get(MsgCode.ACCOUNT_DISABLED.value)["msg"])
                
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
            
            # 生成新的 token
            token_expire = timedelta(minutes=EXPIRE_TIME * 2) if cached_user['type'] != UserType.NORMAL else timedelta(minutes=EXPIRE_TIME)
            token = createToken.create_token(
                {
                    "sub": str(cached_user['id']),
                    "type": cached_user['type'],
                    "login_type": cached_user['login_type']
                }, 
                token_expire
            )
            
            # 更新缓存中的 token
            cached_user['token'] = token
            cached_user['last_time'] = current_time
            cached_user['continuous_days'] = continuous_days
            redis_db.cache_user_info(cached_user)
            
            # 返回用户信息
            response_data = cached_user.copy()
            del response_data['password']
            return HttpStatus.success(
                message=Message.success()["msg"],
                data=response_data
            )
        
        # 2. 如果缓存中没有，从数据库查询
        query = db.query(UserInputs)
        if user_auth.login_type == LoginType.EMAIL:
            if not is_valid_email(user_auth.account):
                return HttpStatus.error(message=Message.get(MsgCode.EMAIL_INVALID_FORMAT.value)["msg"])
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
                return HttpStatus.error(message=Message.get(MsgCode.ACCOUNT_OR_PASSWORD_ERROR.value)["msg"])
            if existing_user.status == UserStatus.DISABLED:
                return HttpStatus.error(message=Message.get(MsgCode.ACCOUNT_DISABLED.value)["msg"])
            
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
        token_expire = timedelta(minutes=EXPIRE_TIME * 2) if existing_user.type != UserType.NORMAL else timedelta(minutes=EXPIRE_TIME)
        token = createToken.create_token(
            {
                "sub": str(existing_user.id),
                "type": int(existing_user.type),
                "login_type": int(existing_user.login_type)
            }, 
            token_expire
        )
        
        # 准备用户数据
        user_data = prepare_user_data(existing_user, token, continuous_days)
        
        # 更新 Redis 缓存
        redis_db.cache_user_info(user_data)
        redis_db.update_login_record(existing_user.id, continuous_days)
        
        # 删除敏感信息
        response_data = user_data.copy()
        del response_data['password']
        
        return HttpStatus.success(
            message=Message.success()["msg"], 
            data=response_data
        )

    except SQLAlchemyError as e:
        db.rollback()
        return HttpStatus.server_error()

@userApp.get('/info', description="获取用户信息", summary="获取用户信息")
async def get_user_info(user_id: int = Depends(createToken.parse_token), db: Session = Depends(getDbSession)):
    """
    获取用户信息
    - 优先从 Redis 缓存获取
    - 如果缓存不存在，从数据库获取并更新缓存
    """
    try:
        if not user_id:
            return HttpStatus.unauthorized(
                message=Message.unauthorized("用户未登录")["msg"],)
            
        # 查找用户
        current_user = db.query(UserInputs).filter(UserInputs.id == user_id).first()
        if not current_user:
            return HttpStatus.error(message=Message.get(MsgCode.USER_NOT_FOUND.value)["msg"])
            
        # 尝试从缓存获取用户信息
        account = current_user.email if current_user.login_type == LoginType.EMAIL else current_user.username
        cached_user = redis_db.get_user_info(account, current_user.login_type)
        
        if cached_user:
            # 从缓存获取登录记录
            login_record = redis_db.get_login_record(current_user.id)
            if login_record:
                cached_user['continuous_days'] = login_record['continuous_days']
            
            # 删除敏感信息
            del cached_user['password']
            return HttpStatus.success(message=Message.success()["msg"])

        
        # 如果缓存不存在，从数据库获取
        login_record = db.query(UserLoginRecord).filter(
            UserLoginRecord.user_id == current_user.id
        ).order_by(UserLoginRecord.login_date.desc()).first()
        
        continuous_days = login_record.continuous_days if login_record else 1
        
        # 准备用户数据
        user_data = prepare_user_data(current_user, None, continuous_days)  # token 为 None，因为这里不需要
        
        # 更新缓存
        redis_db.cache_user_info(user_data)
        if login_record:
            redis_db.update_login_record(current_user.id, continuous_days)
        
        # 删除敏感信息
        del user_data['password']
        return HttpStatus.success(message=Message.success()["msg"], data=user_data)
        
    except Exception as e:
        return HttpStatus.server_error(
            message=Message.error(f"获取用户信息失败: {str(e)}")["msg"],
        )

@userApp.post('/update', description="更新用户信息", summary="更新用户信息")
async def update_user_info(
    user_info: UserInfo, 
    user_id: int = Depends(createToken.parse_token), 
    db: Session = Depends(getDbSession)
):
    """
    更新用户信息
    - 验证用户输入
    - 更新数据库
    - 同步更新 Redis 缓存
    """
    try:
        if not user_id:
            return HttpStatus.unauthorized(
                message=Message.unauthorized("用户未登录")["msg"],
            )
            
        # 查找用户
        current_user = db.query(UserInputs).filter(UserInputs.id == user_id).first()
        if not current_user:
            return HttpStatus.error(message=Message.get(MsgCode.USER_NOT_FOUND.value)["msg"])
        
        # 检查邮箱是否已被使用
        if user_info.email and user_info.email != current_user.email:
            existing = db.query(UserInputs).filter(
                UserInputs.email == user_info.email,
                UserInputs.id != current_user.id
            ).first()
            if existing:
                return HttpStatus.error(message=Message.get(MsgCode.EMAIL_ALREADY_BOUND.value)["msg"])
        
        # 检查用户名是否已被使用
        if user_info.username and user_info.username != current_user.username:
            existing = db.query(UserInputs).filter(
                UserInputs.username == user_info.username,
                UserInputs.id != current_user.id
            ).first()
            if existing:
                return HttpStatus.error(message=Message.get(MsgCode.USERNAME_ALREADY_BOUND.value)["msg"])
        
        # 更新用户信息
        update_fields = {
            k: v for k, v in user_info.dict(exclude_unset=True).items()
            if v is not None and hasattr(current_user, k)
        }
        
        if update_fields:
            # 更新最后修改时间
            update_fields['last_time'] = int(time.time())
            
            # 更新数据库
            for key, value in update_fields.items():
                setattr(current_user, key, value)
            db.commit()
            
            # 清除旧的缓存
            old_account = current_user.email if current_user.login_type == LoginType.EMAIL else current_user.username
            redis_db.clear_user_cache(old_account, current_user.login_type)
            
            # 获取最新的登录记录
            login_record = db.query(UserLoginRecord).filter(
                UserLoginRecord.user_id == current_user.id
            ).order_by(UserLoginRecord.login_date.desc()).first()
            
            continuous_days = login_record.continuous_days if login_record else 1
            
            # 准备新的用户数据
            user_data = prepare_user_data(current_user, None, continuous_days)
            
            # 更新缓存
            new_account = current_user.email if current_user.login_type == LoginType.EMAIL else current_user.username
            redis_db.cache_user_info(user_data)
            
            # 删除敏感信息
            del user_data['password']
            return HttpStatus.success(message=Message.success()["msg"], data=user_data)
        
        return HttpStatus.error(message=Message.get(MsgCode.NO_UPDATE_INFO.value)["msg"])
        
    except ValueError as ve:
        return HttpStatus.error(message=Message.error(str(ve))["msg"])
    except Exception as e:
        db.rollback()
        return HttpStatus.server_error(
            message=Message.error(f"更新用户信息失败: {str(e)}")["msg"],
        )

@userApp.post('/logout', description="用户登出", summary="用户登出")
async def logout(user_id: int = Depends(createToken.parse_token), db: Session = Depends(getDbSession)):
    """
    用户登出
    - 清除用户 Redis 缓存
    - 更新用户最后登出时间
    - 保存登出记录
    """
    try:
        if not user_id:
            return HttpStatus.unauthorized(
                message=Message.unauthorized("用户未登录")["msg"],
            )
            
        # 查找用户
        current_user = db.query(UserInputs).filter(UserInputs.id == user_id).first()
        if not current_user:
            return HttpStatus.error(message=Message.get(MsgCode.USER_NOT_FOUND.value)["msg"])

        current_time = int(time.time())
        
        # 1. 更新用户最后登出时间
        current_user.last_time = current_time
        db.commit()
        
        # 2. 记录登出时间
        logout_record = UserLogoutRecord(
            user_id=current_user.id,
            logout_time=current_time,
            logout_date=date.today()
        )
        db.add(logout_record)
        db.commit()
        
        # 3. 清除 Redis 缓存
        # 清除用户信息缓存
        account = current_user.email if current_user.login_type == LoginType.EMAIL else current_user.username
        redis_db.clear_user_cache(account, current_user.login_type)
        
        # 清除登录记录缓存
        redis_db.clear_login_record(current_user.id)
        
        # 清除 token 缓存（如果有）
        redis_db.clear_token_cache(current_user.id)
        
        return HttpStatus.success(
            message=Message.success("登出成功")["msg"]
        )
        
    except Exception as e:
        db.rollback()
        return HttpStatus.server_error(
            message=Message.error(f"登出失败: {str(e)}")["msg"],
        )

@userApp.post(
    '/bind-email',
    description=ApiDescriptions.BIND_EMAIL.description,
    summary=ApiDescriptions.BIND_EMAIL.summary
)
async def bind_email(
    email: str,
    verify_code: str,
    user_id: int = Depends(createToken.parse_token),
    db: Session = Depends(getDbSession)
):
    """
    绑定邮箱接口
    - 验证邮箱格式
    - 验证验证码
    - 更新用户邮箱信息
    - 更新缓存
    """
    if not is_valid_email(email):
        return HttpStatus.error(
            message=Message.get(MsgCode.EMAIL_INVALID_FORMAT.value)["msg"],
        )

    # 验证验证码
    redis_key = f"email_verify_{email}"
    stored_code = redis_db.get(redis_key)
    if not stored_code or stored_code != verify_code:
        return HttpStatus.error(
            message=Message.get(MsgCode.EMAIL_CODE_INVALID.value)["msg"],
        )

    try:
        # 检查邮箱是否已被其他用户使用
        existing_user = db.query(UserInputs).filter(
            UserInputs.email == email,
            UserInputs.id != user_id
        ).first()
        if existing_user:
            return HttpStatus.error(
                message=Message.get(MsgCode.EMAIL_ALREADY_BOUND.value)["msg"],
            )

        # 更新用户信息
        user = db.query(UserInputs).filter(UserInputs.id == user_id).first()
        if not user:
            return HttpStatus.error(
                message=Message.get(MsgCode.USER_NOT_FOUND.value)["msg"],
            )

        user.email = email
        user.emailCode = EmailStatus.BOUND
        user.last_time = int(time.time())
        db.commit()

        # 更新Redis缓存
        user_data = prepare_user_data(user, "", user.continuous_days)
        redis_db.set(f"user_{user_id}", user_data, EXPIRE_TIME)
        return HttpStatus.success(
            message=Message.get(MsgCode.EMAIL_BIND_SUCCESS.value)["msg"]
        )

    except SQLAlchemyError as e:
        db.rollback()
        return HttpStatus.server_error()

@userApp.post(
    '/send-email-code',
    description=ApiDescriptions.SEND_EMAIL_CODE.description,
    summary=ApiDescriptions.SEND_EMAIL_CODE.summary
)
async def send_email_code(
    email: str,
    user_id: int = Depends(createToken.parse_token),
    db: Session = Depends(getDbSession)
):
    """
    发送邮箱验证码
    - 验证邮箱格式
    - 发送验证码邮件
    """
    if not is_valid_email(email):
        return HttpStatus.error(
            message=Message.get(MsgCode.EMAIL_INVALID_FORMAT.value)["msg"]
        )

    try:
        # 检查发送频率限制
        redis_key = f"email_verify_{email}"
        if redis_db.exists(redis_key):
            return HttpStatus.error(
                message=Message.get(MsgCode.EMAIL_SEND_TOO_FREQUENT.value)["msg"]
            )

        # 发送邮件（包含验证码生成和存储）
        email_result = await sendBindEmail(email, user_id)
        
        if email_result.get("code") != status.HTTP_200_OK:
            # 如果是频率限制错误
            if email_result.get("code") == MsgCode.EMAIL_SEND_TOO_FREQUENT.value:
                return HttpStatus.error(
                    message=Message.get(MsgCode.EMAIL_SEND_TOO_FREQUENT.value)["msg"]
                )
            # 其他发送失败情况
            return HttpStatus.error(
                message=Message.get(MsgCode.EMAIL_SEND_FAILED.value)["msg"]
            )

        return HttpStatus.success(
            message=Message.get(MsgCode.EMAIL_VERIFY_SUCCESS.value)["msg"]
        )

    except Exception as e:
        return HttpStatus.server_error()
