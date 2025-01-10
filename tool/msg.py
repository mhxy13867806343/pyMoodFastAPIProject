from enum import Enum
from typing import Dict, Optional, TypeVar, Generic, Any
from pydantic import BaseModel, Field
from config.error_code import ErrorCode
from config.error_messages import USER_ERROR, SYSTEM_ERROR

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

    @classmethod
    def success(cls, data: Optional[T] = None, message: str = "操作成功", code: int = ErrorCode.SUCCESS) -> "Message[T]":
        """成功响应"""
        return cls(code=code, message=message, data=data)

    @classmethod
    def error(cls, message: Optional[str] = None, code: int = ErrorCode.INTERNAL_ERROR, data: Optional[T] = None) -> "Message[T]":
        """错误响应"""
        if message is None:
            message = USER_ERROR.get("SYSTEM_ERROR", "操作失败")
        return cls(code=code, message=message, data=data)

    @classmethod
    def warning(cls, message: str = "警告", code: int = ErrorCode.BAD_REQUEST, data: Optional[T] = None) -> "Message[T]":
        """警告响应"""
        return cls(code=code, message=message, data=data)

    @classmethod
    def info(cls, message: str = "提示", code: int = ErrorCode.SUCCESS, data: Optional[T] = None) -> "Message[T]":
        """信息响应"""
        return cls(code=code, message=message, data=data)

    @classmethod
    def server_error(cls, message: Optional[str] = None) -> "Message[T]":
        """服务器错误响应"""
        return cls.error(
            message=message or SYSTEM_ERROR["SYSTEM_ERROR"],
            code=ErrorCode.INTERNAL_ERROR
        )

    @classmethod
    def custom(cls, code: int, message: str, data: Optional[T] = None) -> "Message[T]":
        """自定义响应"""
        return cls(code=code, message=message, data=data)