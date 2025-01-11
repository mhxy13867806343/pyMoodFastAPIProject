import datetime
from typing import Optional, Dict, Any
from datetime import timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from jwt.exceptions import InvalidTokenError as JWTError
import bcrypt
from dotenv import load_dotenv
import os
from .validationTools import ValidationError
from config.error_messages import USER_ERROR, SYSTEM_ERROR

# 加载环境变量
load_dotenv()
EnvSECRET_KEY = os.getenv('SECRET_KEY')
EnvEXPIRE_TIME = os.getenv('EXPIRE_TIME')

if not EnvSECRET_KEY:
    raise ValueError(SYSTEM_ERROR["CONFIG_ERROR"])

# JWT配置
SECRET_KEY = EnvSECRET_KEY
ALGORITHM = "HS256"
EXPIRE_TIME = int(EnvEXPIRE_TIME or str(60*60*24*30))  # 默认30天

# OAuth2 scheme配置
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码
    :param plain_password: 明文密码
    :param hashed_password: 加密后的密码
    :return: bool
    """
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except Exception as e:
        raise ValidationError(USER_ERROR["PASSWORD_ERROR"])

def get_password_hash(password: str) -> str:
    """
    获取密码hash
    :param password: 明文密码
    :return: str
    """
    try:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    except Exception as e:
        raise ValidationError(USER_ERROR["PASSWORD_ERROR"])

def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    创建访问令牌
    :param data: 数据
    :param expires_delta: 过期时间
    :return: str
    """
    try:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(seconds=EXPIRE_TIME)
            
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    except Exception as e:
        raise ValidationError(USER_ERROR["TOKEN_CREATE_ERROR"])

def parse_token(token: str = Depends(oauth2_scheme), *, required: bool = True, full_payload: bool = False) -> Any:
    """
    统一的token解析方法，可用于所有token解析场景
    :param token: token字符串
    :param required: 是否必需，如果为True则token无效时抛出异常
    :param full_payload: 是否返回完整的payload
    :return: 根据参数返回不同的值：
            - required=True, full_payload=False: int (user_id)
            - required=True, full_payload=True: Dict (完整payload)
            - required=False, full_payload=False: Optional[int] (user_id或None)
            - required=False, full_payload=True: Optional[Dict] (payload或None)
    
    使用示例：
    1. 必需的user_id（用于需要登录的接口）:
       user_id: int = Depends(lambda token: parse_token(token, required=True))
       
    2. 可选的user_id（用于可以匿名访问的接口）:
       user_id: Optional[int] = Depends(lambda token: parse_token(token, required=False))
    """
    # 如果没有token
    if not token:
        if required:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "message":USER_ERROR["TOKEN_INVALID"],
                    "code":status.HTTP_401_UNAUTHORIZED
                },
                headers={"WWW-Authenticate": "Bearer"},
            )
        return None

    try:
        # 解析token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # 提取用户ID
        user_id = payload.get("sub")
        if not user_id:
            if required:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={
                        "message": USER_ERROR["TOKEN_INVALID"],
                        "code": status.HTTP_401_UNAUTHORIZED
                    },
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return None
            
        # 返回结果
        if full_payload:
            return payload
        return int(user_id)
            
    except JWTError:
        if required:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "message": USER_ERROR["TOKEN_INVALID"],
                    "code": status.HTTP_401_UNAUTHORIZED
                },
                headers={"WWW-Authenticate": "Bearer"},
            )
        return None
    except Exception:
        if required:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "message": USER_ERROR["TOKEN_INVALID"],
                    "code": status.HTTP_401_UNAUTHORIZED
                },
                headers={"WWW-Authenticate": "Bearer"},
            )
        return None