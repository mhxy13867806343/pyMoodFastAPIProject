import string
import uuid
from sqlalchemy import and_, not_, inspect, desc
from sqlalchemy.orm import Session, Query
from typing import Optional, List, Dict, Any, Union, TypeVar, Type, Callable, cast, Tuple
import re
import secrets
import time
import random
from hashlib import md5
from fastapi import status
from datetime import datetime


def get_pagination(
        model,
        session: Session,
        pageNum: int = 1,
        pageSize: int = 20,
        **kwargs
):
    offset = (pageNum - 1) * pageSize
    query = session.query(model)

    # 动态过滤
    query = apply_filters(query, model, **kwargs)

    # 排序、分页
    total = query.count()
    items = query.offset(offset).limit(pageSize).all()

    # 将 SQLAlchemy 模型对象转换为字典
    result_list = []
    for item in items:
        if hasattr(item, 'to_dict'):
            result_list.append(item.to_dict())
        else:
            item_dict = {}
            for column in item.__table__.columns:
                value = getattr(item, column.name)
                if isinstance(value, (datetime.date, datetime.datetime)):
                    value = value.isoformat()
                item_dict[column.name] = value
            result_list.append(item_dict)

    return {
        "total": total,
        "pageNum": pageNum,
        "pageSize": pageSize,
        "data": result_list,
    }


def apply_filters(query, model, **kwargs):
    """
    向查询中动态添加过滤条件。
    :param query: 当前的 SQLAlchemy 查询对象。
    :param model: 要查询的 SQLAlchemy 模型类。
    :param kwargs: 动态过滤条件。
    :return: 过滤后的查询对象。
    """
    print("Filter conditions:", kwargs)  # 调试日志
    
    # 如果没有过滤条件，返回所有记录
    if not kwargs:
        return query
        
    for attr, value in kwargs.items():
        if hasattr(model, attr):
            model_field = getattr(model, attr)
            if isinstance(value, str):
                # 字符串字段使用模糊查询
                query = query.filter(model_field.like(f"%{value}%"))
            else:
                # 非字符串字段使用精确匹配
                query = query.filter(model_field == value)
    
    print("Final SQL:", str(query))  # 调试日志
    return query


def get_total_count(query_obj: Query) -> int:
    """获取查询结果总数"""
    return query_obj.count()

def sysHex4randCode(prefix: str = "DICTITEM_", length: int = 8) -> str:
    """生成指定长度的随机编码"""
    import random
    import string
    
    # 生成随机字符串
    chars = string.ascii_uppercase + string.digits
    random_str = ''.join(random.choice(chars) for _ in range(length))
    
    return f"{prefix}{random_str}"

def generate_dynamic_cookies() -> Dict[str, str]:
    """
    生成动态cookies

    返回:
    Dict[str, str]: 包含各种cookie值的字典
    """
    current_time = int(time.time())
    random_value = random.randint(1000, 9999)

    # 生成动态的 _ga 类型的值
    ga_value = f'GA1.1.{random_value}.{current_time}'

    # 使用 MD5 生成一个假设的会话 ID
    session_id = md5(f"{current_time}{random_value}".encode()).hexdigest()

    return {
        'Culture': 'c%3Dzh%7Cuic%3Dzh',
        '_ga': ga_value,
        '_ga_KSTCY0VQQ2': f'GS1.1.{current_time}.{random_value}.0.0.0',
        'Hm_lvt_00199139cedb22dd93566ef972128f5f': str(current_time),
        'Hm_lpvt_00199139cedb22dd93566ef972128f5f': str(current_time + 300),
        'session_id': session_id
    }

def validate_email(email: str) -> bool:
    """
    验证电子邮件地址是否合法。

    参数:
    email (str): 待验证的电子邮件地址。

    返回:
    bool: 如果电子邮件地址合法，则返回 True；否则返回 False。
    """
    pattern = r'^[A-Za-z0-9\u4e00-\u9fa5]+@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$'
    return bool(re.match(pattern, email))

def httpStatus(code: int = status.HTTP_400_BAD_REQUEST, message: str = "获取失败", data: dict | list = None) -> dict:
    """
    统一的HTTP响应格式
    :param code: HTTP状态码
    :param message: 响应消息
    :param data: 响应数据，可以是字典或列表
    :return: 标准化的响应格式
    """
    if data is None:
        data = {}
        
    return {
        "code": code,
        "message": message,
        "data": data
    }