from enum import Enum
from typing import Dict, Optional, TypeVar, Generic, Any

from fastapi import HTTPException
from pydantic import BaseModel, Field
from starlette import status

from config.error_code import ErrorCode
from config.error_messages import USER_ERROR, SYSTEM_ERROR
from fastapi.responses import JSONResponse

class MsgType(str, Enum):
    """消息类型枚举"""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

T = TypeVar('T')

class Message(BaseModel, Generic[T]):
    """消息处理类"""
    code: int = Field(default=ErrorCode.SUCCESS)
    message: str = Field(default="操作成功")
    data: Optional[T] = None
    headers: Optional[Dict[str, str]] = Field(default=None, exclude=True)

    def dict(self, *args, **kwargs):
        """重写dict方法，在序列化时排除headers为None的情况"""
        d = super().dict(*args, **kwargs)
        if d.get('headers') is None:
            d.pop('headers', None)
        if d.get('data') is None:
            d.pop('data', None)
        return d

    @classmethod
    def success(cls, data: Optional[T] = None, message: str = "操作成功", code: int = ErrorCode.SUCCESS) -> JSONResponse:
        """成功响应"""
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=cls(code=code, message=message, data=data).dict()
        )

    @classmethod
    def error(cls, message: Optional[str] = None, code: int = ErrorCode.INTERNAL_ERROR, data: Optional[T] = None) -> JSONResponse:
        """错误响应"""
        if message is None:
            message = USER_ERROR.get("SYSTEM_ERROR", "操作失败")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=cls(code=code, message=message, data=data).dict()
        )

    @classmethod
    def warning(cls, message: str = "警告", code: int = ErrorCode.BAD_REQUEST, data: Optional[T] = None) -> JSONResponse:
        """警告响应"""
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=cls(code=code, message=message, data=data).dict()
        )

    @classmethod
    def info(cls, message: str = "提示", code: int = ErrorCode.SUCCESS, data: Optional[T] = None) -> JSONResponse:
        """信息响应"""
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=cls(code=code, message=message, data=data).dict()
        )

    @classmethod
    def server_error(cls, message: Optional[str] = None) -> JSONResponse:
        """服务器错误响应"""
        return cls.error(
            message=message or SYSTEM_ERROR["SYSTEM_ERROR"],
            code=ErrorCode.INTERNAL_ERROR
        )

    @classmethod
    def custom(cls, code: int, message: str, data: Optional[T] = None) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=cls(code=code, message=message, data=data).dict()
        )

    @classmethod
    def http_401_exception(cls) -> JSONResponse:
        """
        返回401未授权响应
        :param message: 自定义错误消息，如果不提供则使用默认的TOKEN_INVALID消息
        """
        unauthorized=ErrorCode.UNAUTHORIZED
        message=USER_ERROR.get("TOKEN_EXPIRED")
        response_data={
            "code":unauthorized,
            "message":message
        }
        headers={
            "WWW-Authenticate": "Bearer"
        }
        raise HTTPException(
            detail=response_data,
            headers=headers,
            status_code=unauthorized
        )
