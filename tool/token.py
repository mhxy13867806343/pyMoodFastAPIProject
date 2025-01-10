from typing import Optional, Dict, Union
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status, Security, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from jose import jwt, JWTError
import bcrypt
from dotenv import load_dotenv
import os
from .validationTools import ParamValidator, ValidationError

# 加载环境变量
load_dotenv()

# 常量配置
PWD_CONTEXT = CryptContext(schemes=['bcrypt'], deprecated='auto')
EnvSECRET_KEY = os.getenv('SECRET_KEY')
EnvACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")
if not EnvSECRET_KEY:
    raise ValueError("未找到必须的文件,请联系管理员")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(EnvACCESS_TOKEN_EXPIRE_MINUTES or '43200')  # 默认30天

# OAuth2 scheme配置
oauth_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_password_hash(password: str) -> str:
    """
    使用bcrypt对密码进行哈希处理

    Args:
        password: 原始密码

    Raises:
        ValidationError: 当password验证失败时抛出

    Returns:
        str: 哈希后的密码
    """
    ParamValidator.validate_string(password, "密码")
    
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    使用bcrypt验证密码

    Args:
        plain_password: 原始密码
        hashed_password: 哈希后的密码

    Raises:
        ValidationError: 当参数验证失败时抛出

    Returns:
        bool: 密码是否匹配
    """
    ParamValidator.validate_string(plain_password, "原始密码")
    ParamValidator.validate_string(hashed_password, "哈希密码")
    
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except Exception as e:
        raise ValidationError(f"密码验证失败: {str(e)}")

def create_access_token(
    data: Dict[str, Union[str, int]],
    expires_delta: Optional[Union[timedelta, int]] = None
) -> str:
    """
    创建访问令牌

    Args:
        data: 要编码到令牌中的数据
        expires_delta: 过期时间，可以是timedelta对象或者分钟数

    Raises:
        ValidationError: 当参数验证失败时抛出

    Returns:
        str: JWT令牌
    """
    ParamValidator.validate_dict(data, "data", ["sub"])
    ParamValidator.validate_expires_delta(expires_delta, "过期时间")
    
    to_encode = data.copy()
    
    try:
        if expires_delta is None:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        elif isinstance(expires_delta, int):
            expire = datetime.utcnow() + timedelta(minutes=expires_delta)
        else:
            expire = datetime.utcnow() + expires_delta
            
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, EnvSECRET_KEY, algorithm=ALGORITHM)
    except Exception as e:
        raise ValidationError(f"创建token失败: {str(e)}")

def parse_token(token: str = Depends(oauth_scheme)) -> Optional[int]:
    """
    解析JWT令牌

    Args:
        token: JWT令牌

    Returns:
        Optional[int]: 用户ID，解析失败返回None
    """
    if not token:
        return None
        
    try:
        ParamValidator.validate_string(token, "token")
        payload = jwt.decode(token, EnvSECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            return None
        return int(user_id)
    except (JWTError, ValidationError, ValueError):
        return None

def get_current_user_id(request: Request) -> Optional[int]:
    """
    从请求头中获取当前用户ID

    Args:
        request: FastAPI请求对象

    Returns:
        Optional[int]: 用户ID，获取失败返回None
    """
    if not request:
        return None
        
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None
        
    try:
        ParamValidator.validate_string(auth_header, "Authorization header")
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None
            
        token = parts[1]
        payload = jwt.decode(token, EnvSECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            return None
        return int(user_id)
    except (IndexError, JWTError, ValidationError, ValueError):
        return None