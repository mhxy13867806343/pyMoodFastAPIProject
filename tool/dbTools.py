from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any, Union, TypeVar, Type, Callable, cast
import re
import secrets
import time
import random
from hashlib import md5
def getPistPagenaTion(db:Session,dbms=None,current:int=1,size:int=20)->Optional[List[Dict[str, Any]]]:
    offsetCurrent=(current-1)*size
    array=db.query(dbms).offset(offsetCurrent).limit(size).all()
    return array

#获取总条数
def getPistPagenationTotal(db:Session,dbms=None)->int:
    count=db.query(dbms).count()
    return count
def generate_dynamic_cookies():
    current_time = int(time.time())
    random_value = random.randint(1000, 9999)

    # 生成动态的 _ga 类型的值
    ga_value = f'GA1.1.{random_value}.{current_time}'

    # 使用 MD5 生成一个假设的会话 ID
    session_id = md5(f"{current_time}{random_value}".encode()).hexdigest()

    # 生成时间相关的 Cookie 值
    hm_lvt_value = current_time
    hm_lpvt_value = current_time + 300  # 假设5分钟后过期

    cookies = {
        'Culture': 'c%3Dzh%7Cuic%3Dzh',
        '_ga': ga_value,
        '_ga_KSTCY0VQQ2': f'GS1.1.{current_time}.{random_value}.0.0.0',
        'Hm_lvt_00199139cedb22dd93566ef972128f5f': str(hm_lvt_value),
        'Hm_lpvt_00199139cedb22dd93566ef972128f5f': str(hm_lpvt_value),
        'session_id': session_id
    }
    return cookies
def getValidate_email(email):
    """
    验证电子邮件地址是否合法。

    参数:
    email (str): 待验证的电子邮件地址。

    返回:
    bool: 如果电子邮件地址合法，则返回 True；否则返回 False。
    """
    pattern = r'^[A-Za-z0-9\u4e00-\u9fa5]+@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$'
    return bool(re.match(pattern, email))