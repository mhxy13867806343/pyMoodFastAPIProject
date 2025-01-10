import json
from typing import Tuple, List
from sqlalchemy import or_
import requests
from sqlalchemy.types import TypeDecorator, CHAR
from fastapi import  status
import uuid
import re
import time
import hashlib
from datetime import datetime, timedelta
from tool.dbHeaders import jsHeaders, outerUserAgentHeadersX64
# 通用工具类 正则表达式
toolReg={
    "email_regex":r'^(([^<>()[\]\\.,;:\s@"]+(\.[^<>()[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$',
    "phone_regex":r"^(?:(?:\+|00)86)?1[3-9]\d{9}$",
    "pwd_regex": r"/^\S*(?=\S{6,})(?=\S*\d)(?=\S*[A-Z])(?=\S*[a-z])(?=\S*[!@#$%^&*? ])\S*$/"
}


def performGetRequest(url:str=None, method='get', data=None, json=None):
    if not url:
        return httpStatus(code=status.HTTP_400_BAD_REQUEST, message="请求地址不能为空", data={})
    try:
        if method == 'post':
            response = requests.post(url, headers=outerUserAgentHeadersX64, data=data, json=json)
        elif method == 'get':
            response = requests.get(url, headers=outerUserAgentHeadersX64, json=json,data=None)
        if response.status_code != 200:
            return httpStatus(code=status.HTTP_500_INTERNAL_SERVER_ERROR, message=f"获取数据失败: {response.status_code}", data={})
        return httpStatus(code=status.HTTP_200_OK, message="获取成功", data=response.json())
    except requests.ConnectionError:
        # 处理连接错误
        raise httpStatus(code=status.HTTP_503_SERVICE_UNAVAILABLE, message="服务不可达")
    except requests.Timeout:
        # 处理超时错误
        raise httpStatus(code=status.HTTP_408_REQUEST_TIMEOUT, message="请求超时")
    except requests.RequestException as e:
        # 对于其他请求相关的异常
        raise httpStatus(code=status.HTTP_500_INTERNAL_SERVER_ERROR, message=str(e))
def get_next_year_timestamp():
    current_time = datetime.now()
    next_year_date = current_time.replace(year=current_time.year + 1)
    return int(time.mktime(next_year_date.timetuple()))
class UUIDType(TypeDecorator):
    impl = CHAR

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif isinstance(value, uuid.UUID):
            return str(value)
        else:
            return str(uuid.UUID(value))

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            return uuid.UUID(value)

def httpStatus(code:int=status.HTTP_400_BAD_REQUEST,message:str="获取失败",data:dict={})->dict:
    return {
        "data":{
            "code":code,
            "message":message,
            "result":data
        }
    }
def validate_phone_number(phone_number:int)->bool:
    return validateReg("phone_regex",phone_number)
#密码强度校验，最少6位，包括至少1个大写字母，1个小写字母，1个数字，1个特殊字符
def validate_pwd(pwd_str:str)->bool:
    return validateReg("pwd_regex",pwd_str)

def validateReg(reg:str,txt:str)->bool:
    pattern = toolReg[reg]
    return re.match(pattern, txt) if 1 else 0
def validate_email_str(s:str)->bool:
    return validateReg("email_regex",s)


def validate_encrypt_email(email:str=""):
    result =validate_email_str(email)
    if not result:
        return httpStatus(message="邮箱格式不正确", data={})
    # 分割邮箱地址为用户名和域名
    user, domain = email.split('@')

    # 根据不同的用户名长度进行处理
    if len(user) > 2:
        # 如果用户名长度大于2，保留第一个和最后一个字符，中间用星号替换
        encrypted_user = user[0] + '*' * (len(user) - 2) + user[-1]
    elif len(user) == 2:
        # 如果用户名长度等于2，保留第一个字符，第二个字符用星号替换
        encrypted_user = user[0] + '*'
    else:
        # 如果用户名长度为1，直接使用用户名，不加密
        encrypted_user = user

    # 合并加密后的用户名和域名
    encrypted_email = encrypted_user + '@' + domain
    return encrypted_email
def validate_phone_input(phone: str)->dict or None:
    if not phone:
        return httpStatus(message="手机号码不能为空", data={})
    if not validate_phone_number(phone):
        return httpStatus(message="手机号格式不合法", data={})
    if len(phone) != 11:
        return httpStatus(message="手机号必须为11位", data={})

    return None  # 如果验证通过，返回 None

def createUuid(name,time,pwd):
    data="{}{}{}".format(name,time,pwd)
    d=uuid.uuid5(uuid.NAMESPACE_DNS, data)
    return d



def createMd5Pwd(pwd:str):
    m = hashlib.md5()
    m.update(pwd.encode('utf-8'))
    return m.hexdigest()


def getListAll(db=None, cls=None, name: str = '', status: int = 0, pageNo: int = 1, pageSize: int = 20):
    size = (pageNo - 1) * pageSize

    # 如果name为空字符串，即没有提供搜索关键词，则忽略name的筛选条件
    if name:
        result = db.query(cls).filter(or_(cls.name.like(f"%{name}%"), cls.status == status)).offset(size).limit(
            pageSize).all()
    else:  # 如果没有提供name，只根据status筛选
        result = db.query(cls).filter(cls.status == status).offset(size).limit(pageSize).all()

    return result


def getListAllTotal(db=None, cls=None, name: str = '', status: int = 0) -> int:
    # 类似地处理总数查询
    if name:
        count = db.query(cls).filter(or_(cls.name.like(f"%{name}%"), cls.status == status)).count()
    else:
        count = db.query(cls).filter(cls.status == status).count()

    return count
def getJsonStatic(static:str=""):
    try:
        with open(static, "r", encoding="utf-8") as json_file:
            data = json.load(json_file)
        return httpStatus(data=data, code=status.HTTP_200_OK, message="获取成功")
    except FileNotFoundError:
        return httpStatus(message='未找到相关资源', code=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return httpStatus(message=str(e), code=status.HTTP_500_INTERNAL_SERVER_ERROR)