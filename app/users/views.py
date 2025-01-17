import datetime
import string
import random

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
import time
from datetime import date, timedelta
import re
from typing import Optional, Dict, Any, Union, Tuple
from sqlalchemy import or_, text
from extend.db import LOCSESSION

from config.api_descriptions import ApiDescriptions
from config.error_messages import USER_ERROR, SYSTEM_ERROR, LOG_MESSAGES
from tool.dbConnectionConfig import sendBindEmail, getVerifyEmail, generate_random_code
from tool.getLogger import globalLogger
from tool.msg import Message
from config.error_code import ErrorCode
from tool.param_validator import validate_params
from tool.token import EXPIRE_TIME
from tool.validationTools import ValidationError
from tool import token as createToken
from .model import UserAuth, UserInfo
from models.user.model import UserInputs, UserType, UserStatus, UserLoginRecord, LoginType, UserSex, UserLvNext
from tool.db import getDbSession
from tool.dbRedis import RedisDB
from app.users.schemas import (
    UserUpdateRequest, EmailBindRequest, EmailCodeRequest, SignatureRequest, 
    CheckNameRequest, CheckNameResponse, UserLvResponse, UserExpUpdateRequest
)
import os
import hashlib
from datetime import datetime
from typing import List
from fastapi import Request
from pathlib import Path
from tool.upload import FileUploader
from config.upload_config import UPLOAD_TYPES, UPLOAD_DIR, IMAGE_CONFIG

# 获取图片配置中的限制
MAX_FILE_SIZE = IMAGE_CONFIG["max_size"]
ALLOWED_EXTENSIONS = IMAGE_CONFIG["allowed_extensions"]

# 加载环境变量
redis_db = RedisDB()
userApp = APIRouter(tags=[ApiDescriptions.USER_TAGS])

# 管理员账号配置
ADMIN_ACCOUNTS = {
    # 用户名登录的管理员
    'admin': {'type': UserType.ADMIN, 'login_type': LoginType.USERNAME},
    'superadmin': {'type': UserType.SUPER, 'login_type': LoginType.USERNAME},
    # 邮箱登录的管理员
    'admin@example.com': {'type': UserType.ADMIN, 'login_type': LoginType.EMAIL},
    'super@example.com': {'type': UserType.SUPER, 'login_type': LoginType.EMAIL}
}

def get_file_md5(file_content: bytes) -> str:
    """计算文件内容的MD5值"""
    return hashlib.md5(file_content).hexdigest()

def is_valid_file(filename: str, filesize: int) -> tuple[bool, str]:
    """
    检查文件是否有效
    :return: (是否有效, 错误信息)
    """
    # 检查文件大小
    if filesize > MAX_FILE_SIZE:
        return False, "文件大小不能超过10MB"
    
    # 检查文件扩展名
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"只支持以下格式: {', '.join(ALLOWED_EXTENSIONS)}"
    
    return True, ""

def ensure_upload_dir(user_id: int) -> Path:
    """
    确保上传目录存在
    :return: 上传目录路径
    """
    # 创建日期目录
    today = datetime.now().strftime("%Y-%m-%d")
    avatar_dir = UPLOAD_DIR / today / f"avatar-{user_id}"
    avatar_dir.mkdir(parents=True, exist_ok=True)
    return avatar_dir

def is_valid_email(email: str) -> bool:
    """验证邮箱格式"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

async def record_user_login(db: Session, user: UserInputs) -> None:
    """
    记录用户登录
    :param db: 数据库会话
    :param user: 用户对象
    """
    try:
        today = date.today()
        current_time = int(time.time())

        # 查找最近的登录记录
        last_record = db.query(UserLoginRecord).filter(
            UserLoginRecord.user_uid == user.uid
        ).order_by(UserLoginRecord.login_date.desc()).first()

        continuous_days = 1
        if last_record:
            # 计算日期差
            days_diff = (today - last_record.login_date).days
            if days_diff == 1:  # 连续登录
                continuous_days = last_record.continuous_days + 1
            elif days_diff == 0:  # 今天已经登录过
                return

        # 创建新的登录记录
        new_record = UserLoginRecord(
            user_uid=user.uid,
            login_date=today,
            login_time=current_time,
            continuous_days=continuous_days
        )
        db.add(new_record)
        db.commit()

    except Exception as e:
        db.rollback()
        globalLogger.error(f"记录用户登录失败: {str(e)}")
        raise

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
        "is_registered": user.is_registered,
        "signature": user.signature or ""  # 确保签名字段永远不会是 None
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
        globalLogger.exception(f"{USER_ERROR['EMAIL_VERIFY_CODE_ERROR']}: {str(e)}")
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
        globalLogger.exception(f"{USER_ERROR['EMAIL_ALREADY_BOUND']}: {str(e)}")
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
        globalLogger.exception(f"{USER_ERROR['EMAIL_SEND_ERROR']}: {str(e)}")
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

        # 准备更新的数据
        update_data = {}
        if request.username is not None:
            update_data['username'] = request.username
        if request.email is not None:
            update_data['email'] = request.email
        if request.phone is not None:
            update_data['phone'] = request.phone
        if request.name is not None:
            update_data['name'] = request.name
        if request.sex is not None:
            update_data['sex'] = UserSex(request.sex)
        if request.location is not None:
            update_data['location'] = request.location
        if request.avatar is not None:
            update_data['avatar'] = request.avatar
        if request.is_registered is not None:
            update_data['is_registered'] = request.is_registered
        if request.signature is not None:  # 允许设置空字符串
            update_data['signature'] = request.signature

        # 更新时间戳
        current_time = int(time.time())
        update_data['last_time'] = current_time

        try:
            # 1. 先从 Redis 获取当前用户数据
            cached_user_data = await redis_db.get_user_data(request.uid)
            
            if cached_user_data:
                # 2. 更新 Redis 中的数据
                cached_user_data.update(update_data)
                await redis_db.set_user_data(request.uid, cached_user_data)

            # 3. 更新数据库
            for key, value in update_data.items():
                setattr(db_user, key, value)
            
            db.commit()
            db.refresh(db_user)
            
            # 4. 如果 Redis 更新失败但数据库更新成功，重新设置 Redis
            if not cached_user_data:
                user_data = get_user_data(db_user, include_private=True)
                await redis_db.set_user_data(request.uid, user_data)
            
            return get_user_data(db_user, include_private=True)

        except Exception as e:
            # 如果发生错误，回滚数据库并清除 Redis 缓存
            db.rollback()
            await redis_db.clear_user_cache(request.uid)
            raise e

    except Exception as e:
        db.rollback()
        globalLogger.exception(f"{USER_ERROR['USER_UPDATE_FAILED']}: {str(e)}")
        return None

@userApp.post(
    "/auth",
    response_model=Message[Dict[str, Any]],
    summary=ApiDescriptions.AUTH["summary"],
    description=ApiDescriptions.AUTH["description"]
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
            
            # 检查用户状态
            status_check = check_cached_user_status(cached_user)
            if status_check:
                return status_check
            
            # 生成新的token
            token_expire = timedelta(seconds=EXPIRE_TIME * 2) if cached_user['type'] != UserType.NORMAL.value else timedelta(seconds=EXPIRE_TIME)
            token = createToken.create_token(
                {
                    "sub": cached_user["uid"],
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
            await record_user_login(db, cached_user)
            
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
            status_check, user = get_check_user_status(existing_user.uid, db)
            if status_check:
                return status_check
            
            # 检查是否需要更新用户类型（比如普通用户被加入管理员白名单）
            admin_info = ADMIN_ACCOUNTS.get(user_auth.account)
            if admin_info and admin_info['login_type'] == existing_user.login_type and existing_user.type != admin_info['type']:
                existing_user.type = admin_info['type']
                db.commit()

        # 处理登录记录并获取连续登录天数
        await record_user_login(db, existing_user)
        
        # 更新用户最后登录时间
        existing_user.last_time = current_time
        db.commit()

        # 生成token，管理员token有效期更长
        token_expire = timedelta(seconds=EXPIRE_TIME * 2) if existing_user.type != UserType.NORMAL else timedelta(seconds=EXPIRE_TIME)
        token = createToken.create_token(
            {
                "sub": existing_user.uid,
                "type": int(existing_user.type),
                "login_type": int(existing_user.login_type)
            }, 
            token_expire
        )
        
        # 准备用户数据（包含密码用于缓存）
        user_data = prepare_user_data(existing_user, token, 1, include_password=True)
        
        # 更新 Redis 缓存
        redis_db.cache_user_info(user_data)
        
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
    summary=ApiDescriptions.GET_USER_INFO["summary"],
    description=ApiDescriptions.GET_USER_INFO["description"]
)
async def get_current_user_info(
    current_user_uid: str = Depends(lambda: createToken.parse_token(required=True)),
    db: Session = Depends(getDbSession)
):
    """
    获取当前登录用户的详细信息
    - 从 token 中获取用户 ID
    - 返回用户的所有可见信息
    """
    try:
        # 获取并检查用户
        status_check, user = get_check_user_status(current_user_uid, db)
        if status_check:
            return status_check

        # 获取用户的连续登录记录数
        login_record = db.query(UserLoginRecord).filter(
            UserLoginRecord.user_uid == user.uid
        ).order_by(UserLoginRecord.login_date.desc()).first()
        
        # 获取用户数据（包含私密信息）
        user_data = get_user_data(user, include_private=True)
        user_data["continuous_days"] = login_record.continuous_days if login_record else 1

        return Message.success(data=user_data)
    except Exception as e:
        globalLogger.error(f"{SYSTEM_ERROR['SYSTEM_ERROR']}: {str(e)}")
        return Message.error(message=SYSTEM_ERROR["SYSTEM_ERROR"])

@userApp.get(
    "/info/{user_id}",
    response_model=Message[Dict[str, Any]],
    summary=ApiDescriptions.GET_USER_INFO_BY_ID["summary"],
    description=ApiDescriptions.GET_USER_INFO_BY_ID["description"]
)
@validate_params('user_id')
async def get_user_info(
    user_id: int,
    current_user_uid: Optional[str] = Depends(lambda: createToken.parse_token(required=False)),
    db: Session = Depends(getDbSession)
):
    """
    获取指定用户的公开信息
    - 如果是获取自己的信息，返回所有信息
    - 如果是获取其他用户的信息，只返回公开信息
    - 如果未登录，只返回最基本的公开信息
    """
    try:
        # 获取并检查用户
        status_check, user = get_check_user_status(str(user_id), db)
        if status_check:
            return status_check

        # 判断是否是查看自己的信息
        is_self = current_user_uid and str(user_id) == current_user_uid

        # 获取用户数据
        user_data = get_user_data(user, include_private=is_self)
        return Message.success(data=user_data)
    except Exception as e:
        globalLogger.error(f"{SYSTEM_ERROR['SYSTEM_ERROR']}: {str(e)}")
        return Message.error(message=SYSTEM_ERROR["SYSTEM_ERROR"])

@userApp.put(
    "/update",
    response_model=Message[Dict[str, Any]],
    summary=ApiDescriptions.UPDATE_USER["summary"],
    description=ApiDescriptions.UPDATE_USER["description"]
)
async def update_user(
    request: UserUpdateRequest,
    current_user_uid: str = Depends(lambda: createToken.parse_token(required=True)),
    db: Session = Depends(getDbSession)
):
    """
    更新用户信息
    - 需要登录
    - 只能更新自己的信息
    - 支持更新：昵称、性别、头像、位置、签名
    """
    try:
        # 参数验证
        if not request.uid:
            return Message.error(
                message=USER_ERROR["PARAM_ERROR"],
                code=ErrorCode.INVALID_PARAMS
            )

        # 确保只能更新自己的信息
        if request.uid != current_user_uid:
            return Message.error(
                message=USER_ERROR["PERMISSION_DENIED"],
                code=ErrorCode.FORBIDDEN
            )

        # 更新用户信息
        updated_user = await update_user_info(db, request)
        if not updated_user:
            return Message.error(
                message=USER_ERROR["USER_UPDATE_FAILED"],
                code=ErrorCode.INTERNAL_ERROR
            )

        return Message.success(
            message=USER_ERROR["USER_UPDATE_SUCCESS"],
            data=updated_user
        )

    except ValidationError as e:
        return Message.error(
            message=str(e),
            code=ErrorCode.INVALID_PARAMS
        )
    except Exception as e:
        globalLogger.exception(f"{SYSTEM_ERROR['SYSTEM_ERROR']}: {str(e)}")
        return Message.error(
            message=SYSTEM_ERROR["SYSTEM_ERROR"],
            code=ErrorCode.INTERNAL_ERROR
        )

@userApp.post(
    "/logout",
    response_model=Message,
    summary=ApiDescriptions.LOGOUT["summary"],
    description=ApiDescriptions.LOGOUT["description"]
)
async def logout(
    current_user_uid: str = Depends(lambda: createToken.parse_token(required=True)),
    db: Session = Depends(getDbSession)
):
    """
    用户登出
    - 需要登录
    - 清除 Redis 缓存
    - 更新最后登录时间
    """
    try:
        # 清除 Redis 缓存
        redis_db.clear_user_cache(current_user_uid)
        
        # 更新用户最后登录时间
        user = db.query(UserInputs).filter(UserInputs.uid == current_user_uid).first()
        if user:
            user.last_time = int(time.time())
            db.commit()
        
        return Message.success(message=USER_ERROR["LOGOUT_SUCCESS"])
    except Exception as e:
        globalLogger.exception(f"{USER_ERROR['LOGOUT_FAILED']}: {str(e)}")
        return Message.error(
            message=USER_ERROR["LOGOUT_FAILED"],
            code=ErrorCode.INTERNAL_ERROR
        )

@userApp.post(
    "/email/bind",
    response_model=Message[Dict[str, Any]],
    summary=ApiDescriptions.BIND_EMAIL["summary"],
    description=ApiDescriptions.BIND_EMAIL["description"]
)
async def bind_email(
    request: EmailBindRequest,
    current_user_uid: str = Depends(lambda: createToken.parse_token(required=True)),
    db: Session = Depends(getDbSession)
):
    """
    绑定用户邮箱
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
        success = await bind_user_email(db, current_user_uid, request.email)
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
    summary=ApiDescriptions.SEND_EMAIL_CODE["summary"],
    description=ApiDescriptions.SEND_EMAIL_CODE["description"]
)
async def send_email_code(
    request: EmailCodeRequest,
    current_user_uid: str = Depends(lambda: createToken.parse_token(required=True))
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

@userApp.post(
    "/upload/avatar",
    response_model=Message[Dict[str, Any]],
    summary=ApiDescriptions.UPLOAD_AVATAR["summary"],
    description=ApiDescriptions.UPLOAD_AVATAR["description"]
)
async def upload_avatar(
    request: Request,
    use_oss: bool = False,
    current_user_uid: str = Depends(lambda: createToken.parse_token(required=True)),
    db: Session = Depends(getDbSession)
):
    """
    上传用户头像
    - 支持图片格式：.png、.jpg、.jpeg、.webp
    - 文件大小限制：10MB
    """
    try:
        # 获取上传的文件
        form = await request.form()
        if "file" not in form:
            return Message.error(message=USER_ERROR["NO_FILE_UPLOADED"], code=ErrorCode.BAD_REQUEST)
            
        file = form["file"]
        if not hasattr(file, "filename"):
            return Message.error(message=USER_ERROR["INVALID_FILE"], code=ErrorCode.BAD_REQUEST)

        # 使用 FileUploader 处理上传
        uploader = FileUploader(current_user_uid)
        file_content = await file.read()
        success, message, path = await uploader.save_file(file_content, file.filename)
        
        if not success:
            return Message.error(message=message, code=ErrorCode.BAD_REQUEST)
        
        # 更新用户头像路径
        user = db.query(UserInputs).filter(UserInputs.uid == current_user_uid).first()
        if not user:
            return Message.error(message=USER_ERROR["USER_NOT_FOUND"], code=ErrorCode.USER_NOT_FOUND)
        
        user.avatar = path
        db.commit()
        
        return Message.success(
            data={"url": path},
            message=USER_ERROR["AVATAR_UPLOAD_SUCCESS"]
        )
        
    except Exception as e:
        globalLogger.exception(f"{LOG_MESSAGES['UPLOAD_AVATAR_FAILED']}: {str(e)}")
        return Message.error(message=USER_ERROR["UPLOAD_FAILED"], code=ErrorCode.INTERNAL_ERROR)

@userApp.post(
    "/upload/batch",
    response_model=Message[Dict[str, List]],
    summary=ApiDescriptions.BATCH_UPLOAD["summary"],
    description=ApiDescriptions.BATCH_UPLOAD["description"]
)
async def batch_upload(
    request: Request,
    use_oss: bool = False,
    current_user_uid: str = Depends(lambda: createToken.parse_token(required=True))
):
    """
    批量上传文件
    - 支持图片格式：.png、.jpg、.jpeg、.webp（最多9张）
    - 支持视频格式：.mp4、.mov、.avi（最多1个）
    - 图片大小限制：10MB
    - 视频大小限制：100MB
    """
    try:
        form = await request.form()
        files = []
        for key in form.keys():
            if key.startswith("file"):
                file = form[key]
                if hasattr(file, "filename"):
                    files.append(file)

        if not files:
            return Message.error(message=USER_ERROR["NO_FILE_UPLOADED"], code=ErrorCode.BAD_REQUEST)

        # 使用 FileUploader 处理上传
        uploader = FileUploader(current_user_uid)
        result = await uploader.process_files(files)

        # 检查是否有成功上传的文件
        if not result["success"]:
            # 如果所有文件都失败了
            if result["failed"]:
                # 返回第一个错误信息
                return Message.error(
                    message=result["failed"][0]["error"],
                    code=ErrorCode.BAD_REQUEST,
                    data=result
                )
            return Message.error(message=USER_ERROR["NO_FILE_UPLOADED"], code=ErrorCode.BAD_REQUEST)

        # 如果有部分文件失败
        if result["failed"]:
            return Message(
                code=ErrorCode.PARTIAL_SUCCESS,
                message=USER_ERROR["PARTIAL_UPLOAD_SUCCESS"],
                data=result
            )

        # 所有文件都成功
        return Message.success(
            data=result,
            message=USER_ERROR["UPLOAD_SUCCESS"]
        )

    except Exception as e:
        globalLogger.exception(f"{LOG_MESSAGES['BATCH_UPLOAD_FAILED']}: {str(e)}")
        return Message.error(message=USER_ERROR["UPLOAD_FAILED"], code=ErrorCode.INTERNAL_ERROR)

@userApp.get(
    "/signature",
    summary=ApiDescriptions.GET_USER_SIGNATURE["summary"],
    description=ApiDescriptions.GET_USER_SIGNATURE["description"]
)
async def get_signature(
    current_user_uid: str = Depends(lambda: createToken.parse_token(required=True)),
    db: Session = Depends(getDbSession)
):
    """
    获取当前用户的签名
    - 需要登录
    - 只返回当前用户的签名信息
    """
    try:
        status_check, user = get_check_user_status(current_user_uid, db)
        if status_check:
            return status_check
        
        return Message.ok(data={
            "signature": user.signature or ""
        })

    except SQLAlchemyError as e:
        globalLogger.error(f"{LOG_MESSAGES['DATABASE_ERROR']}: {str(e)}")
        return Message.error(message=SYSTEM_ERROR["DATABASE_ERROR"], code=ErrorCode.INTERNAL_ERROR)
    except Exception as e:
        globalLogger.error(f"{LOG_MESSAGES['GET_SIGNATURE_ERROR']}: {str(e)}")
        return Message.error(message=SYSTEM_ERROR["SYSTEM_ERROR"], code=ErrorCode.INTERNAL_ERROR)

@userApp.post(
    "/signature",
    summary=ApiDescriptions.SET_USER_SIGNATURE["summary"],
    description=ApiDescriptions.SET_USER_SIGNATURE["description"]
)
async def set_signature(
    request: SignatureRequest,
    current_user_uid: str = Depends(lambda: createToken.parse_token(required=True)),
    db: Session = Depends(getDbSession)
):
    """设置当前用户的签名"""
    try:
        status_check, user = get_check_user_status(current_user_uid, db)
        if status_check:
            return status_check
        
        # 验证签名长度
        if request.signature and len(request.signature) > 32:
            return Message.error(
                message=USER_ERROR["SIGNATURE_TOO_LONG"],
                code=ErrorCode.INVALID_PARAMS
            )

        # 更新签名
        user.signature = request.signature
        db.commit()

        return Message.ok(data={
            "signature": user.signature or ""
        })

    except SQLAlchemyError as e:
        db.rollback()
        globalLogger.error(f"{LOG_MESSAGES['DATABASE_ERROR']}: {str(e)}")
        return Message.error(message=SYSTEM_ERROR["DATABASE_ERROR"], code=ErrorCode.INTERNAL_ERROR)
    except Exception as e:
        globalLogger.error(f"{LOG_MESSAGES['SET_SIGNATURE_ERROR']}: {str(e)}")
        return Message.error(message=SYSTEM_ERROR["SYSTEM_ERROR"], code=ErrorCode.INTERNAL_ERROR)

def generate_name_suggestions(name: str, db: Session) -> List[str]:
    """
    生成用户名建议
    :param name: 原始用户名
    :param db: 数据库会话
    :return: 建议名称列表
    """
    suggestions = []
    max_suggestions = 20  # 最多返回20个建议
    
    # 创建一个查询来一次性获取所有已存在的名称
    existing_names = set(
        row[0] for row in 
        db.query(UserInputs.name)
        .filter(UserInputs.name.like(f"{name}%"))
        .all()
    )
    
    # 数字后缀（0-25）
    for i in range(0, 26):
        if len(suggestions) >= max_suggestions:
            break
        suggestion = f"{name}{i}"
        if suggestion not in existing_names:
            suggestions.append(suggestion)
    
    # 字母后缀（大小写字母）
    for suffix in string.ascii_letters:
        if len(suggestions) >= max_suggestions:
            break
        suggestion = f"{name}{suffix}"
        if suggestion not in existing_names:
            suggestions.append(suggestion)
    
    # 年份后缀
    if len(suggestions) < max_suggestions:
        current_year = datetime.now().year
        suggestion = f"{name}{current_year}"
        if suggestion not in existing_names:
            suggestions.append(suggestion)
    
    # 随机字母数字组合（如果建议数量还不够）
    while len(suggestions) < max_suggestions:
        # 生成2位随机字符（字母+数字）
        suffix = ''.join(random.choices(string.ascii_letters + string.digits, k=2))
        suggestion = f"{name}{suffix}"
        if suggestion not in existing_names and suggestion not in suggestions:
            suggestions.append(suggestion)
    
    return suggestions[:max_suggestions]

@userApp.post(
    "/check-name",
    response_model=CheckNameResponse,
    summary=ApiDescriptions.POST_USER_CHECK_NAME["summary"],
    description=ApiDescriptions.POST_USER_CHECK_NAME["description"]
)
async def check_name(
    request: CheckNameRequest,
        current_user_uid: str = Depends(lambda: createToken.parse_token(required=True)),
    db: Session = Depends(getDbSession)
):
    try:
        status_check, user = get_check_user_status(current_user_uid, db)
        if status_check:
            return status_check
        
        # 检查名称是否已存在
        existing_user = db.query(UserInputs).filter(UserInputs.name == request.name).first()
        
        if not existing_user:
            return CheckNameResponse(available=True, suggestions=[])
        
        # 如果名称已存在，生成建议
        suggestions = generate_name_suggestions(request.name, db)
        return CheckNameResponse(available=False, suggestions=suggestions)

    except Exception as e:
        globalLogger.error(f"{SYSTEM_ERROR['SYSTEM_ERROR']}: {str(e)}")
        return Message.error(message=SYSTEM_ERROR["SYSTEM_ERROR"])

@userApp.put(
    "/change-name",
    summary=ApiDescriptions.PUT_USER_CHANGE_NAME_["summary"],
    description=ApiDescriptions.PUT_USER_CHANGE_NAME_["description"]
)
async def update_name(
    request: CheckNameRequest,
    current_user_uid: str = Depends(lambda: createToken.parse_token(required=True)),
    db: Session = Depends(getDbSession)
):
    try:
        status_check, user = get_check_user_status(current_user_uid, db)
        if status_check:
            return status_check
        
        # 检查新名称是否已存在
        if db.query(UserInputs).filter(
            UserInputs.name == request.name,
            UserInputs.uid != current_user_uid
        ).first():
            suggestions = generate_name_suggestions(request.name, db)
            return Message.error(
                message=USER_ERROR["NAME_ALREADY_EXISTS"],
                data={"suggestions": suggestions}
            )

        # 更新用户名称
        user.name = request.name
        db.commit()

        return Message.ok(data={"name": user.name})

    except SQLAlchemyError as e:
        db.rollback()
        globalLogger.error(f"{SYSTEM_ERROR['SYSTEM_ERROR']}: {str(e)}")
        return Message.error(message=SYSTEM_ERROR["DATABASE_ERROR"])
    except Exception as e:
        globalLogger.error(f"{SYSTEM_ERROR['SYSTEM_ERROR']}: {str(e)}")
        return Message.error(message=SYSTEM_ERROR["SYSTEM_ERROR"])

@userApp.get(
    "/level",
    summary=ApiDescriptions.GET_USER_LEVEL_["summary"],
    description=ApiDescriptions.GET_USER_LEVEL_["description"]
)
async def get_user_level(
    current_user_uid: str = Depends(lambda: createToken.parse_token(required=True)),
    db: Session = Depends(getDbSession)
):
    """获取用户等级信息"""
    try:
        status_check, user = get_check_user_status(current_user_uid, db)
        if status_check:
            return status_check
        
        # 获取用户等级信息
        user_lv = db.query(UserLvNext).filter(UserLvNext.user_uid == current_user_uid).first()

        # 如果用户没有等级记录，创建一个
        if not user_lv:
            user_lv = UserLvNext(user_uid=current_user_uid)
            db.add(user_lv)
            db.commit()
            db.refresh(user_lv)

        # 获取下一级所需经验
        level_info = user_lv.get_level_by_exp(user_lv.exp)
        data={
            "lv": user_lv.lv,
            "max_lv": user_lv.max_lv,
            "exp": user_lv.exp,
            "next_lv": user_lv.next_lv,
            "exp_to_next_lv": level_info['exp_to_next_lv']
        }
        return Message.success(data=data)
    
    except SQLAlchemyError as e:
        globalLogger.error(f"{SYSTEM_ERROR['DATABASE_ERROR']}: {str(e)}")
        return Message.error(message=SYSTEM_ERROR["DATABASE_ERROR"])
    except Exception as e:
        globalLogger.error(f"{SYSTEM_ERROR['DATABASE_ERROR']}: {str(e)}")
        return Message.error(message=SYSTEM_ERROR["SYSTEM_ERROR"])

@userApp.put(
    "/level/exp",
    summary=ApiDescriptions.PUT_USER_EXP_["summary"],
    description=ApiDescriptions.PUT_USER_EXP_["description"]
)
async def update_user_exp(
    request: UserExpUpdateRequest,
    current_user_uid: str = Depends(lambda: createToken.parse_token(required=True)),
    db: Session = Depends(getDbSession)
):
    """更新用户经验值"""
    try:
        status_check, user = get_check_user_status(current_user_uid, db)
        if status_check:
            return status_check
        
        # 获取用户等级信息
        user_lv = db.query(UserLvNext).filter(UserLvNext.user_uid == current_user_uid).first()
        
        # 如果用户没有等级记录，创建一个
        if not user_lv:
            user_lv = UserLvNext(user_uid=current_user_uid)
            db.add(user_lv)
            db.commit()
            db.refresh(user_lv)
        
        # 更新经验值
        level_info = user_lv.update_exp(request.exp_gained)
        db.commit()
        data = {
            "lv": user_lv.lv,
            "max_lv": user_lv.max_lv,
            "exp": user_lv.exp,
            "next_lv": user_lv.next_lv,
            "exp_to_next_lv": level_info['exp_to_next_lv']
        }
        return Message.success(data=data)

    except SQLAlchemyError as e:
        db.rollback()
        globalLogger.error(f"{SYSTEM_ERROR['DATABASE_ERROR']}: {str(e)}")
        return Message.error(message=SYSTEM_ERROR["DATABASE_ERROR"])
    except Exception as e:
        db.rollback()
        globalLogger.error(f"{SYSTEM_ERROR['DATABASE_ERROR']}: {str(e)}")
        return Message.error(message=SYSTEM_ERROR["SYSTEM_ERROR"])

def get_check_user_status(user_id: str, db: Session) -> Tuple[Optional[Message], Optional[Union[UserInputs, Dict]]]:
    """
    检查用户状态
    :param user_id: 用户ID
    :param db: 数据库会话
    :return: (错误消息, 用户对象) 如果有错误返回 (错误消息, None)，否则返回 (None, 用户对象)
    """
    # 查找用户
    user = db.query(UserInputs).filter(UserInputs.uid == user_id).first()
    if not user:
        return Message.error(message=USER_ERROR["USER_NOT_FOUND"]), None

    # 检查用户状态
    if user.type == UserType.NORMAL and user.status == UserStatus.DISABLED:
        return Message.error(
            code=ErrorCode.USER_DISABLED.value,
            message=USER_ERROR["USER_DISABLED"]
        ), None
    
    return None, user

def check_cached_user_status(user_data: Dict) -> Optional[Message]:
    """
    检查缓存用户状态
    :param user_data: 用户数据字典
    :return: 如果用户状态异常返回错误消息，否则返回 None
    """
    if user_data["type"] == UserType.NORMAL.value and user_data["status"] == UserStatus.DISABLED.value:
        return Message.error(
            code=ErrorCode.USER_DISABLED.value,
            message=USER_ERROR["USER_DISABLED"]
        )
    return None
