from datetime import datetime, timedelta
import secrets
import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr
from fastapi import status
from tool.dbRedis import RedisDB
from tool.emailTools import emailTools
from tool.msg import Message, MsgCode
from tool.classDb import HttpStatus
import random
import string
from typing import Dict, Any, Optional

redis_db = RedisDB()

def generate_random_code(length: int = 6) -> str:
    """
    生成指定长度的随机验证码
    包含大小写字母和数字
    """
    all_chars = string.ascii_letters + string.digits
    return ''.join(random.choice(all_chars) for _ in range(length))

async def sendBindEmail(from_email: str, uid: int = 0) -> Dict[str, Any]:
    """
    发送邮箱绑定验证码
    Args:
        from_email: 发送者邮箱
        uid: 用户ID
    Returns:
        Dict: 包含发送结果的字典
    """
    try:
        now = datetime.now()
        tempkey = f"email_verify_{uid}_{from_email}"
        
        # 检查发送频率
        check = redis_db.get_with_expiry_check(tempkey)
        if check and 'timestamp' in check:
            last_sent = datetime.fromtimestamp(float(check['timestamp']))
            if (now - last_sent) < timedelta(minutes=5):
                return HttpStatus.error(
                    message=Message.get(MsgCode.EMAIL_SEND_TOO_FREQUENT.value)["msg"]
                )

        # 生成验证码
        code = generate_random_code()
        
        # 存储验证码
        redis_db.set_with_expiry(
            tempkey, 
            {
                "code": code, 
                "timestamp": now.timestamp(),
                "email": from_email
            },
            expire_time=5,
            time_unit="minutes"
        )

        # 构建邮件内容
        html_content = f"""
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; font-family: Arial, sans-serif;">
            <h2 style="color: #333;">邮箱验证码</h2>
            <p style="color: #666;">您的验证码是：</p>
            <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <span style="color: #e74c3c; font-size: 24px; font-weight: bold;">{code}</span>
            </div>
            <p style="color: #666;">验证码有效期为5分钟，请尽快使用。</p>
            <p style="color: #999; font-size: 12px;">如果这不是您的操作，请忽略此邮件。</p>
        </div>
        """
        
        message = MIMEText(html_content, 'html', 'utf-8')
        
        # 获取邮件配置
        to_email = emailTools.get('to_email')
        server_host = emailTools.get('to_serverHost')
        server_port = emailTools.get('to_serverPort')
        main_password = emailTools.get('to_main_password')

        # 设置邮件头
        message['To'] = formataddr(('用户', to_email))
        message['From'] = formataddr(('验证码服务', from_email))
        message['Subject'] = "邮箱验证码"

        # 发送邮件
        server = None
        try:
            server = smtplib.SMTP_SSL(server_host, server_port)
            server.login(from_email, main_password)
            server.sendmail(from_email, [to_email], message.as_string())
            return HttpStatus.success(
                message=Message.get(MsgCode.EMAIL_VERIFY_SUCCESS.value)["msg"]
            )
        except smtplib.SMTPException as e:
            return HttpStatus.error(
                message=Message.get(MsgCode.EMAIL_SEND_FAILED.value)["msg"]
            )
        finally:
            if server:
                server.quit()
                
    except Exception as e:
        return HttpStatus.server_error()

async def getVerifyEmail(email: str, code: str, uid: int = 0) -> Dict[str, Any]:
    """
    验证邮箱验证码
    Args:
        email: 邮箱地址
        code: 验证码
        uid: 用户ID
    Returns:
        Dict: 包含验证结果的字典
    """
    tempkey = f"email_verify_{uid}_{email}"
    code_data = redis_db.get_with_expiry_check(tempkey)

    if not code_data:
        return HttpStatus.error(
            message=Message.get(MsgCode.EMAIL_CODE_EXPIRED.value)["msg"]
        )

    stored_code = code_data.get("code")
    stored_email = code_data.get("email")
    timestamp = code_data.get("timestamp")

    if not all([stored_code, stored_email, timestamp]):
        return HttpStatus.error(
            message=Message.get(MsgCode.EMAIL_CODE_INVALID.value)["msg"]
        )

    # 验证邮箱匹配
    if stored_email != email:
        return HttpStatus.error(
            message=Message.get(MsgCode.EMAIL_CODE_INVALID.value)["msg"]
        )

    # 验证码匹配检查
    if stored_code != code:
        return HttpStatus.error(
            message=Message.get(MsgCode.EMAIL_CODE_INVALID.value)["msg"]
        )

    # 检查是否过期
    try:
        code_timestamp = datetime.fromtimestamp(float(timestamp))
        if datetime.now() - code_timestamp > timedelta(minutes=5):
            redis_db.del_with_expiry_check(tempkey)
            return HttpStatus.error(
                message=Message.get(MsgCode.EMAIL_CODE_EXPIRED.value)["msg"]
            )
    except (TypeError, ValueError):
        return HttpStatus.server_error()

    # 验证成功后删除验证码
    redis_db.del_with_expiry_check(tempkey)
    
    return HttpStatus.success(
        message=Message.get(MsgCode.EMAIL_VERIFY_SUCCESS.value)["msg"]
    )
