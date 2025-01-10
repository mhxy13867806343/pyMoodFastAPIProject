import redis
import schedule
import  time
import tool.statusTool as statusTool
from tool.classDb import httpStatus


rd={
    "key1":"user:",
    "key2":"user-temp:"
}

class RedisDB:

    def __init__(self, host='localhost', port=6379, db=0, decode_responses=True):
        self.redis_client = redis.Redis(host=host, port=port, db=db, decode_responses=decode_responses)

    def is_running(self):
        try:
            return self.redis_client.ping()
        except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError):
            return False
    def __repr__(self):
        return f'<RedisDB {self.redis_client}>'
    def get(self, key: str=''):
        """从Redis获取用户信息。"""
        data = f"{rd.get('key1')}{key}"
        user_data = self.redis_client.hgetall(data)
        if not user_data:
            return None
        return user_data  # 直接返回用户数据

    def set(self, key: str = '', value: dict = {}):
        """将用户信息存储到Redis。"""
        data = f"{rd.get('key1')}{key}"
        user_data = self.get(key)
        if user_data is None:  # 如果用户不存在
            # 注意：使用hset并传入字典
            self.redis_client.hset(data, mapping=value)
        else:  # 如果用户已存在
            # 更新用户信息
            self.redis_client.hmset(data, value)
        # 设置过期时间，例如24小时。这一步是可选的。
        self.redis_client.expire(data, statusTool.EXPIRE_TIME)
        return httpStatus(message="存储成功", data={})


    def delete(self, key: str=''):
        """删除用户信息。"""
        data = f"{rd.get('key1')}{key}"
        if self.get(key) is not None:  # 如果用户存在
            self.redis_client.delete(data)
            return httpStatus(message="删除成功", data={})
        return httpStatus(message="用户未找到,删除失败", data={}, code=statusTool.statusCode[12000])

    def set_with_expiry(self, key: str = '', value: dict = {}, expire_time: int = 5, time_unit: str = 'minutes'):
        """存储数据并设置自定义过期时间和单位，默认为5分钟"""
        data = f"{rd.get('key2')}{key}"
        # 计算过期时间的秒数
        if time_unit == 'minutes':
            expire_seconds = expire_time * 60
        elif time_unit == 'hours':
            expire_seconds = expire_time * 3600
        elif time_unit == 'days':
            expire_seconds = expire_time * 86400
        else:
            expire_seconds = expire_time  # 如果单位是秒
        self.redis_client.hset(data, mapping=value)
        self.redis_client.expire(data, expire_seconds)
        return httpStatus(message="存储成功，带有过期时间", data={})

    def get_with_expiry_check(self, key: str = ''):
        if not key:
            return httpStatus(message="请输入key", data={}, code=statusTool.statusCode[130001])
        """获取数据及其剩余的过期时间"""
        data = f"{rd.get('key2')}{key}"
        user_data = self.redis_client.hgetall(data)
        if user_data:
            ttl = self.redis_client.ttl(data)

            user_data['ttl'] = ttl
            return user_data
        else:
            return httpStatus(message="数据不存在或已过期", data={}, code=statusTool.statusCode[12000])
    def del_with_expiry_check(self, key: str = ''):
        if not key:
            return httpStatus(message="请输入key", data={}, code=statusTool.statusCode[130001])
        """删除数据并检查剩余的过期时间"""
        data = f"{rd.get('key2')}{key}"
        if self.get_with_expiry_check(key) is not None:  # 如果临时数据存在
            self.redis_client.delete(data)
            return httpStatus(message="删除成功", data={})
        return httpStatus(message="数据不存在或已过期", data={}, code=statusTool.statusCode[130001])

def check_redis():
    redis_db = RedisDB()
    if not redis_db.is_running():
        return httpStatus(message="redis未运行,请运行", data={}, code=statusTool.statusCode[60000])

#
# schedule.every(600).seconds.do(check_redis) # 每隔600秒检查一次 Redis 是否运行
#
# while True:
#     schedule.run_pending()
#     time.sleep(1)