from enum import Enum
from typing import Dict, Optional, TypeVar, Generic, Any, ClassVar
from pydantic import BaseModel, Field

class MsgType(Enum):
    """消息类型枚举"""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

class MsgCode(Enum):
    """消息码枚举"""
    SUCCESS = "200"
    FAILED = "500"
    INVALID_PARAMS = "400"
    NOT_FOUND = "404"
    UNAUTHORIZED = "401"
    FORBIDDEN = "403"
    
    # 认证相关
    AUTH_SUCCESS = "2001"
    AUTH_FAILED = "4001"
    TOKEN_INVALID = "4002"
    TOKEN_EXPIRED = "4003"
    ACCOUNT_DISABLED = "4004"
    
    # 密码相关
    PWD_WEAK = "4101"
    PWD_EMPTY = "4102"
    PWD_UPDATE_SUCCESS = "2002"
    PWD_UPDATE_FAILED = "4103"
    
    # 用户相关
    USER_NOT_FOUND = "4201"
    USER_EXISTS = "4202"
    USER_UPDATE_SUCCESS = "2003"
    USER_UPDATE_FAILED = "4203"
    NICKNAME_EMPTY = "4204"
    NICKNAME_NO_CHANGE = "4205"
    
    # 邮箱相关
    EMAIL_EMPTY = "4301"
    EMAIL_INVALID_FORMAT = "4302"
    EMAIL_CODE_INVALID = "4303"
    EMAIL_ALREADY_BOUND = "4304"
    EMAIL_SEND_FAILED = "4305"
    EMAIL_CODE_EXPIRED = "4306"
    EMAIL_SEND_TOO_FREQUENT = "4307"
    EMAIL_BIND_SUCCESS = "2004"
    EMAIL_VERIFY_SUCCESS = "2005"
    
    # 签名相关
    SIGNATURE_NOT_FOUND = "4401"
    SIGNATURE_TOO_LONG = "4402"
    SIGNATURE_ADD_SUCCESS = "2006"
    SIGNATURE_ADD_FAILED = "4403"
    SIGNATURE_UPDATE_SUCCESS = "2007"
    SIGNATURE_UPDATE_FAILED = "4404"

T = TypeVar('T')

class Message(BaseModel, Generic[T]):
    """消息处理类"""
    
    code: str = Field(default=MsgCode.SUCCESS.value)
    message: str = Field(default="操作成功")
    data: Optional[T] = None

    messages: ClassVar[Dict[str, str]] = {
        # 通用消息
        MsgCode.SUCCESS.value: "操作成功",
        MsgCode.FAILED.value: "操作失败",
        MsgCode.INVALID_PARAMS.value: "无效的参数",
        MsgCode.NOT_FOUND.value: "资源不存在",
        MsgCode.UNAUTHORIZED.value: "未授权",
        MsgCode.FORBIDDEN.value: "禁止访问",
        
        # 认证相关
        MsgCode.AUTH_SUCCESS.value: "登录成功",
        MsgCode.AUTH_FAILED.value: "登录失败",
        MsgCode.TOKEN_INVALID.value: "登录信息已失效，请重新登录",
        MsgCode.TOKEN_EXPIRED.value: "登录信息已过期，请重新登录",
        MsgCode.ACCOUNT_DISABLED.value: "当前用户已被禁用，请联系管理员",
        
        # 密码相关
        MsgCode.PWD_WEAK.value: "密码强度太弱，最少6位，包括至少1个大写字母，1个小写字母，1个数字，1个特殊字符",
        MsgCode.PWD_EMPTY.value: "密码不能为空",
        MsgCode.PWD_UPDATE_SUCCESS.value: "密码修改成功",
        MsgCode.PWD_UPDATE_FAILED.value: "密码修改失败",
        
        # 用户相关
        MsgCode.USER_NOT_FOUND.value: "用户不存在",
        MsgCode.USER_EXISTS.value: "当前帐号已存在，请直接登录",
        MsgCode.USER_UPDATE_SUCCESS.value: "用户信息更新成功",
        MsgCode.USER_UPDATE_FAILED.value: "用户信息更新失败",
        MsgCode.NICKNAME_EMPTY.value: "昵称不能为空",
        MsgCode.NICKNAME_NO_CHANGE.value: "昵称未发生变化",
        
        # 邮箱相关
        MsgCode.EMAIL_EMPTY.value: "邮箱不能为空，请输入邮箱地址",
        MsgCode.EMAIL_INVALID_FORMAT.value: "邮箱格式不正确",
        MsgCode.EMAIL_CODE_INVALID.value: "验证码错误或已过期",
        MsgCode.EMAIL_ALREADY_BOUND.value: "该邮箱已被其他用户绑定",
        MsgCode.EMAIL_SEND_FAILED.value: "邮件发送失败",
        MsgCode.EMAIL_CODE_EXPIRED.value: "验证码已过期",
        MsgCode.EMAIL_SEND_TOO_FREQUENT.value: "验证码发送过于频繁，请稍后再试",
        MsgCode.EMAIL_BIND_SUCCESS.value: "邮箱绑定成功",
        MsgCode.EMAIL_VERIFY_SUCCESS.value: "验证码发送成功",
        
        # 签名相关
        MsgCode.SIGNATURE_NOT_FOUND.value: "签名不存在",
        MsgCode.SIGNATURE_TOO_LONG.value: "签名过长",
        MsgCode.SIGNATURE_ADD_SUCCESS.value: "签名添加成功",
        MsgCode.SIGNATURE_ADD_FAILED.value: "签名添加失败",
        MsgCode.SIGNATURE_UPDATE_SUCCESS.value: "签名更新成功",
        MsgCode.SIGNATURE_UPDATE_FAILED.value: "签名更新失败"
    }

    @classmethod
    def success(cls, data: Optional[T] = None, message: Optional[str] = None) -> "Message[T]":
        """成功响应"""
        return cls(
            code=MsgCode.SUCCESS.value,
            message=message or cls.messages[MsgCode.SUCCESS.value],
            data=data
        )

    @classmethod
    def error(cls, code: str = MsgCode.FAILED.value, message: Optional[str] = None) -> "Message[T]":
        """错误响应"""
        return cls(
            code=code,
            message=message or cls.messages.get(code, cls.messages[MsgCode.FAILED.value])
        )

    @classmethod
    def server_error(cls, message: Optional[str] = None) -> "Message[T]":
        """服务器错误响应"""
        return cls(
            code=MsgCode.FAILED.value,
            message=message or cls.messages[MsgCode.FAILED.value],
        )

    @classmethod
    def custom(cls, code: str, message: str, data: Optional[T] = None) -> "Message[T]":
        """自定义响应"""
        return cls(code=code, message=message, data=data)