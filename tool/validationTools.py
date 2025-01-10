from typing import Any, Optional, Type, Dict, Union
from datetime import timedelta

class ValidationError(ValueError):
    """自定义验证错误"""
    pass

class ParamValidator:
    """参数验证工具类"""
    
    @staticmethod
    def validate_not_empty(value: Any, param_name: str, expected_type: Optional[Type] = None) -> None:
        """
        验证参数不为空且类型正确

        Args:
            value: 要验证的值
            param_name: 参数名称
            expected_type: 期望的类型（可选）

        Raises:
            ValidationError: 当验证失败时抛出
        """
        if not value:
            raise ValidationError(f"{param_name}不能为空")
            
        if expected_type and not isinstance(value, expected_type):
            raise ValidationError(f"{param_name}必须是{expected_type.__name__}类型")

    @staticmethod
    def validate_string(value: Any, param_name: str) -> None:
        """
        验证字符串参数

        Args:
            value: 要验证的值
            param_name: 参数名称

        Raises:
            ValidationError: 当验证失败时抛出
        """
        ParamValidator.validate_not_empty(value, param_name, str)

    @staticmethod
    def validate_dict(value: Any, param_name: str, required_keys: Optional[list] = None) -> None:
        """
        验证字典参数

        Args:
            value: 要验证的值
            param_name: 参数名称
            required_keys: 必需的键列表

        Raises:
            ValidationError: 当验证失败时抛出
        """
        ParamValidator.validate_not_empty(value, param_name, dict)
        
        if required_keys:
            missing_keys = [key for key in required_keys if key not in value]
            if missing_keys:
                raise ValidationError(f"{param_name}中缺少必需的字段: {', '.join(missing_keys)}")

    @staticmethod
    def validate_expires_delta(value: Optional[Union[timedelta, int]], param_name: str) -> None:
        """
        验证过期时间参数

        Args:
            value: 要验证的值
            param_name: 参数名称

        Raises:
            ValidationError: 当验证失败时抛出
        """
        if value is None:
            return
            
        if isinstance(value, int):
            if value <= 0:
                raise ValidationError(f"{param_name}必须大于0")
        elif isinstance(value, timedelta):
            if value.total_seconds() <= 0:
                raise ValidationError(f"{param_name}必须大于0")
        else:
            raise ValidationError(f"{param_name}必须是整数或timedelta类型")
