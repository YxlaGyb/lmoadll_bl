# -*- coding: utf-8 -*-
import smtplib
import asyncio
import logging
from email.mime.text import MIMEText
from email.utils import formataddr
from magic.utils.TomlConfig import GLOBAL_CONFIG, load_global_config

def sendMailSync(subject: str, receivers: list[str], html: str) -> bool:
    """同步发送邮件的核心逻辑"""
    load_global_config()
    _smtp = GLOBAL_CONFIG.get("smtp", {})
    server_host = str(_smtp.get('MAIL_SERVER', ''))
    port = int(_smtp.get('MAIL_PORT', 465))
    user = str(_smtp.get('MAIL_USERNAME', ''))
    password = str(_smtp.get('MAIL_PASSWORD', ''))
    sender_name = str(_smtp.get("MAIL_SENDER_NAME", "LMOADLL"))

    msg = MIMEText(html, 'html', 'utf-8')
    msg['From'] = formataddr((sender_name, user))
    msg['To'] = ", ".join(receivers)
    msg['Subject'] = subject

    try:
        with smtplib.SMTP_SSL(server_host, port) as server:
            server.login(user, password)
            server.sendmail(user, receivers, msg.as_string())
        return True
    except Exception as e:
        logging.error(f"邮件发送失败: {e}")
        return False

async def sendMailAsync(subject: str, receivers: list[str], html: str) -> bool:
    """异步发送邮件接口"""
    return await asyncio.to_thread(sendMailSync, subject, receivers, html)
