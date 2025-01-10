from enum import Enum
from typing import Dict, Optional

class MsgType(Enum):
    """消息类型枚举"""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

class MsgCode(Enum):
    """消息代码枚举"""
    # 通用消息
    SUCCESS = "0"
    FAILED = "1"
    INVALID_PARAMS = "2"
    NOT_FOUND = "3"
    UNAUTHORIZED = "4"
    FORBIDDEN = "5"
    
    # 认证相关
    AUTH_SUCCESS = "100"
    AUTH_FAILED = "101"
    TOKEN_INVALID = "102"
    TOKEN_EXPIRED = "103"
    ACCOUNT_DISABLED = "104"
    
    # 密码相关
    PWD_WEAK = "200"
    PWD_EMPTY = "201"
    PWD_UPDATE_SUCCESS = "202"
    PWD_UPDATE_FAILED = "203"
    
    # 用户相关
    USER_NOT_FOUND = "300"
    USER_EXISTS = "301"
    USER_UPDATE_SUCCESS = "302"
    USER_UPDATE_FAILED = "303"
    NICKNAME_EMPTY = "304"
    NICKNAME_NO_CHANGE = "305"
    
    # 邮箱相关
    EMAIL_EMPTY = "400"
    EMAIL_INVALID = "401"
    EMAIL_NOT_BOUND = "402"
    EMAIL_ALREADY_BOUND = "403"
    EMAIL_VERIFY_EMPTY = "404"
    EMAIL_VERIFY_EXPIRED = "405"
    EMAIL_BIND_SUCCESS = "406"
    EMAIL_BIND_FAILED = "407"
    
    # 签名相关
    SIGNATURE_NOT_FOUND = "500"
    SIGNATURE_TOO_LONG = "501"
    SIGNATURE_ADD_SUCCESS = "502"
    SIGNATURE_ADD_FAILED = "503"
    SIGNATURE_UPDATE_SUCCESS = "504"
    SIGNATURE_UPDATE_FAILED = "505"

class Message:
    """消息处理类"""
    
    _messages: Dict[str, str] = {
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
        MsgCode.EMAIL_INVALID.value: "邮箱格式不正确，请重新输入",
        MsgCode.EMAIL_NOT_BOUND.value: "您的用户信息中未有邮箱地址，请先添加邮箱地址",
        MsgCode.EMAIL_ALREADY_BOUND.value: "此邮箱已绑定到其他帐户，请先解除绑定",
        MsgCode.EMAIL_VERIFY_EMPTY.value: "验证码不能为空",
        MsgCode.EMAIL_VERIFY_EXPIRED.value: "验证码已失效，请重新获取",
        MsgCode.EMAIL_BIND_SUCCESS.value: "邮箱绑定成功",
        MsgCode.EMAIL_BIND_FAILED.value: "邮箱绑定失败",
        
        # 签名相关
        MsgCode.SIGNATURE_NOT_FOUND.value: "未找到签名内容",
        MsgCode.SIGNATURE_TOO_LONG.value: "签名内容最大长度为64个字符",
        MsgCode.SIGNATURE_ADD_SUCCESS.value: "签名添加成功",
        MsgCode.SIGNATURE_ADD_FAILED.value: "签名添加失败",
        MsgCode.SIGNATURE_UPDATE_SUCCESS.value: "签名更新成功",
        MsgCode.SIGNATURE_UPDATE_FAILED.value: "签名更新失败",
    }

    @classmethod
    def get(cls, code: str, msg: Optional[str] = None) -> Dict[str, str]:
        """
        获取消息

        Args:
            code: 消息代码
            msg: 可选的自定义消息

        Returns:
            Dict[str, str]: 包含代码和消息的字典
        """
        return {
            "code": code,
            "msg": msg or cls._messages.get(code, "未知错误")
        }

    @classmethod
    def success(cls, msg: Optional[str] = None) -> Dict[str, str]:
        """快捷方法：成功消息"""
        return cls.get(MsgCode.SUCCESS.value, msg)

    @classmethod
    def error(cls, msg: Optional[str] = None) -> Dict[str, str]:
        """快捷方法：错误消息"""
        return cls.get(MsgCode.FAILED.value, msg)

    @classmethod
    def not_found(cls, msg: Optional[str] = None) -> Dict[str, str]:
        """快捷方法：未找到消息"""
        return cls.get(MsgCode.NOT_FOUND.value, msg)

    @classmethod
    def invalid_params(cls, msg: Optional[str] = None) -> Dict[str, str]:
        """快捷方法：无效参数消息"""
        return cls.get(MsgCode.INVALID_PARAMS.value, msg)

    @classmethod
    def unauthorized(cls, msg: Optional[str] = None) -> Dict[str, str]:
        """快捷方法：未授权消息"""
        return cls.get(MsgCode.UNAUTHORIZED.value, msg)