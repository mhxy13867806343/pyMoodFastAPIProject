import string
import uuid

from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any, Union, TypeVar, Type, Callable, cast
import re
import secrets
import time
import random
from hashlib import md5
from fastapi import status

def get_pagination(
    db: Session,
    model: Any,
    page: int = 1,
    page_size: int = 20
) -> Optional[List[Dict[str, Any]]]:
    """
    获取分页数据

    参数:
    db (Session): 数据库会话
    model: 数据库模型
    page (int): 当前页码，默认为1
    page_size (int): 每页数量，默认为20

    返回:
    List: 分页后的数据列表
    """
    offset = (page - 1) * page_size
    return db.query(model).offset(offset).limit(page_size).all()

def get_total_count(db: Session, model: Any) -> int:
    """
    获取总条数

    参数:
    db (Session): 数据库会话
    model: 数据库模型

    返回:
    int: 总条数
    """
    return db.query(model).count()

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
def sysHex4randCode(sdict:str="sys_dict_DICTITEM_")->str:
    alphabet = string.ascii_letters
    random_letters_with_duplicates = ''.join(random.choices(alphabet, k=4))
    code = f"{sdict}{uuid.uuid4().hex}_{random_letters_with_duplicates}"
    return code