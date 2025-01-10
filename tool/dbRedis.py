import redis
import time
from datetime import date, datetime
from tool.statusTool import EXPIRE_TIME
from tool.classDb import httpStatus

REDIS_KEYS = {
    "USER_INFO": "user:info:",    # 用户基本信息，key格式：user:info:{account}:{login_type}
    "USER_LOGIN": "user:login:",  # 用户登录记录
    "USER_TEMP": "user:temp:"     # 临时数据
}

class RedisDB:
    def __init__(self, host='localhost', port=6379, db=0, decode_responses=True):
        self.redis_client = redis.Redis(host=host, port=port, db=db, decode_responses=decode_responses)

    def is_running(self):
        """检查 Redis 是否正常运行"""
        try:
            return self.redis_client.ping()
        except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError):
            return False

    def cache_user_info(self, user_data: dict):
        """
        缓存用户信息
        :param user_data: 用户数据，必须包含 login_type 和对应的登录标识（email 或 username）
        """
        login_type = user_data.get('login_type')
        account = user_data.get('email' if login_type == 0 else 'username')
        if not account:
            return False
            
        key = f"{REDIS_KEYS['USER_INFO']}{account}:{login_type}"
        # 转换数值类型为字符串，避免 Redis 存储问题
        data = {k: str(v) if isinstance(v, (int, bool)) else v for k, v in user_data.items()}
        self.redis_client.hmset(key, data)
        self.redis_client.expire(key, EXPIRE_TIME * 60)  # 转换为秒
        return True

    def get_user_info(self, account: str, login_type: int) -> dict:
        """
        获取用户缓存信息
        :param account: 登录账号（邮箱或用户名）
        :param login_type: 登录类型（0: 邮箱, 1: 用户名）
        :return: 用户信息字典或 None
        """
        key = f"{REDIS_KEYS['USER_INFO']}{account}:{login_type}"
        data = self.redis_client.hgetall(key)
        if not data:
            return None
            
        # 转换特定字段为正确的类型
        type_conversion = {
            'id': int,
            'type': int,
            'create_time': int,
            'last_time': int,
            'status': int,
            'emailCode': int,
            'sex': int,
            'continuous_days': int,
            'login_type': int,
            'is_admin': lambda x: x.lower() == 'true',
            'is_super_admin': lambda x: x.lower() == 'true'
        }
        
        return {
            k: type_conversion[k](v) if k in type_conversion else v 
            for k, v in data.items()
        }

    def update_login_record(self, user_id: int, continuous_days: int):
        """
        更新用户登录记录
        :param user_id: 用户ID
        :param continuous_days: 连续登录天数
        """
        key = f"{REDIS_KEYS['USER_LOGIN']}{user_id}"
        today = date.today().isoformat()
        
        # 保存登录记录
        login_data = {
            'last_login_date': today,
            'last_login_time': str(int(time.time())),
            'continuous_days': str(continuous_days)
        }
        self.redis_client.hmset(key, login_data)
        self.redis_client.expire(key, 86400 * 2)  # 2天过期
        
        # 添加到登录日期集合
        date_set_key = f"{key}:dates"
        self.redis_client.sadd(date_set_key, today)
        self.redis_client.expire(date_set_key, 86400 * 32)  # 保存32天的登录记录

    def get_login_record(self, user_id: int) -> dict:
        """
        获取用户登录记录
        :param user_id: 用户ID
        :return: 登录记录字典
        """
        key = f"{REDIS_KEYS['USER_LOGIN']}{user_id}"
        data = self.redis_client.hgetall(key)
        if not data:
            return None
            
        # 获取登录日期集合
        date_set_key = f"{key}:dates"
        login_dates = list(self.redis_client.smembers(date_set_key))
        
        return {
            'last_login_date': data['last_login_date'],
            'last_login_time': int(data['last_login_time']),
            'continuous_days': int(data['continuous_days']),
            'login_dates': sorted(login_dates)  # 最近32天的登录日期列表
        }

    def clear_user_cache(self, account: str, login_type: int):
        """
        清除用户缓存
        :param account: 登录账号
        :param login_type: 登录类型
        """
        key = f"{REDIS_KEYS['USER_INFO']}{account}:{login_type}"
        self.redis_client.delete(key)

def check_redis():
    redis_db = RedisDB()
    if not redis_db.is_running():
        return httpStatus(message="redis未运行,请运行", data={}, code=60000)