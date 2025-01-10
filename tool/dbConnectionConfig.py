from datetime import datetime, timedelta
import secrets
import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr
from fastapi import status
from tool.dbRedis import RedisDB
from tool.emailTools import emailTools
import random
import string

redis_db = RedisDB()

def generate_random_code():
    all_chars = string.ascii_letters + string.digits  # 包含所有字母和数字
    return ''.join(random.choice(all_chars) for _ in range(6))

def sendBindEmail(from_email: str = "", uid: int = 0):
    now = datetime.now()
    tempkey = f"{uid}-{from_email}"
    check = redis_db.get_with_expiry_check(tempkey)

    # 确保从 Redis 获取的数据包含 'timestamp' 字段
    if check and 'timestamp' in check:
        try:
            last_sent_timestamp = float(check['timestamp'])
            last_sent = datetime.fromtimestamp(last_sent_timestamp)
            if (now - last_sent) < timedelta(minutes=5):
                return {
                    "code": -80008,
                    "result": {},
                    "message": "验证码已发送到您的邮箱中去了，请再5分钟后再试"
                }
        except ValueError:
            return {
                "code": -80009,
                "result": {},
                "message": "时间戳错误，无法计算时间差"
            }

    code = generate_random_code()

    # 存储验证码时使用当前时间的时间戳
    redis_db.set_with_expiry(tempkey, {"code": code, "timestamp": now.timestamp()},
                             expire_time=5, time_unit="minutes")

    message = MIMEText(f"\n您的验证码是:<a href='#' style='color:red'> {code}</a>,如果过期或者使用成功后，将不能再使用了哦!", 'html', 'utf-8')
    to_email = emailTools.get('to_email')
    server_host = emailTools.get('to_serverHost')
    server_port = emailTools.get('to_serverPort')
    main_password = emailTools.get('to_main_password')

    message['To'] = formataddr(('Recipient Name', to_email))
    message['From'] = formataddr(('Current User', from_email))
    message['Subject'] = "发送您的验证码"

    try:
        server = smtplib.SMTP_SSL(server_host, server_port)
        server.login(from_email, main_password)
        server.sendmail(from_email, [to_email], message.as_string())
        return {"code": status.HTTP_200_OK, "result": {}, "message": "发送成功"}
    except smtplib.SMTPException as e:
        return {"code": -800, "result": {}, "message": f"发送失败: {str(e)}"}
    finally:
        server.quit()


async def getVerifyEmail(email: str = "", code: str = "", uid: int = 0):
    tempkey = f"{uid}-{email}"
    code_data = redis_db.get_with_expiry_check(tempkey)

    if not code_data:
        return {
            "code": -800,
            "message": "验证码不存在或已过期"
        }

    # 获取timestamp，并确保它不是None
    timestamp = code_data.get("timestamp")
    if timestamp is None:
        return {
            "code": -801,
            "message": "您的验证码有问题哦, 请重新获取"
        }

    # 将字符串时间戳转换为datetime对象
    try:
        code_timestamp = datetime.fromtimestamp(float(timestamp))
    except (TypeError, ValueError) as e:
        return {
            "code": -802,
            "message": f"时间戳格式错误: {e}"
        }

    # 检查验证码是否在5分钟内
    if datetime.now() - code_timestamp > timedelta(minutes=5):
        # 如果超时，则删除验证码数据
        redis_db.del_with_expiry_check(tempkey)
        return {
            "code": -803,
            "message": "验证码已过期"
        }

    # 检查验证码是否正确
    if code_data.get('code') == code:
        redis_db.del_with_expiry_check(tempkey)
        return {
            "code": status.HTTP_200_OK,
            "message": "验证成功"
        }

    return {
        "code": -804,
        "message": "验证码错误"
    }

