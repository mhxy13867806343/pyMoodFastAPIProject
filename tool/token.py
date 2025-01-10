from typing import Optional, Dict, Union
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status, Security, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
import bcrypt
from dotenv import load_dotenv
import os
from .validationTools import ParamValidator, ValidationError
from tool.classDb import HttpStatus
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

def get_current_user_optional(token: str = Depends(oauth2_scheme)) -> Optional[Dict]:
    """
    获取当前用户（可选）
    :param token: token
    :return: Optional[Dict]
    """
    if not token:
        return None
        
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            return None
            
        token_data = {
            "user_id": user_id,
            "account": payload.get("account"),
            "login_type": payload.get("login_type")
        }
        return token_data
    except JWTError:
        return None
    except Exception as e:
        return None

def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict:
    """
    获取当前用户（必需）
    :param token: token
    :return: Dict
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=USER_ERROR["TOKEN_INVALID"],
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    try:
        ParamValidator.validate_string(token, "token")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=USER_ERROR["TOKEN_INVALID"],
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        token_data = {
            "user_id": user_id,
            "account": payload.get("account"),
            "login_type": payload.get("login_type")
        }
        return token_data
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=USER_ERROR["TOKEN_EXPIRED"],
            headers={"WWW-Authenticate": "Bearer"},
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=USER_ERROR["TOKEN_INVALID"],
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_token_from_cookie(request: Request) -> Optional[Dict]:
    """
    从cookie中获取token
    :param request: Request
    :return: Optional[Dict]
    """
    try:
        authorization = request.cookies.get("Authorization")
        if not authorization:
            return None
            
        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None
            
        token = parts[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            return None
            
        token_data = {
            "user_id": user_id,
            "account": payload.get("account"),
            "login_type": payload.get("login_type")
        }
        return token_data
    except JWTError:
        return None
    except Exception as e:
        return None