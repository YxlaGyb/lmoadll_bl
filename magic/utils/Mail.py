# -*- coding: utf-8 -*-
#lmoadll_bl platform
#
#@copyright  Copyright (c) 2025 lmoadll_bl team
#@license  GNU General Public License 3.0
"""用于处理和加载 Mail 的操作"""

import tomllib
import logging
from quart import Quart
# from quart_mail import Mail
from magic.utils.TomlConfig import CONFIG_PATH
from magic.middleware.errorhandler import handle_errors


mail = Mail()
MAIL_SENDER_NAME = "数数洞洞"
SMTP_CONFIG = {}


@handle_errors("初始化Quart-Mail失败")
def init_mail(app: Quart):
    for key, value in SMTP_CONFIG.items():
        app.config[key] = value
    app.config['MAIL_DEBUG'] = False
    mail.init_app(app)


def load_matl_config():
    """加载邮箱配置""" 
    global MAIL_SENDER_NAME, SMTP_CONFIG
    default_username = ""
    
    try:
        with open(CONFIG_PATH, "rb") as f:
            config = tomllib.load(f)
        
        if "smtp" in config and "MAIL_SENDER_NAME" in config["smtp"]:
            MAIL_SENDER_NAME = config["smtp"]["MAIL_SENDER_NAME"]
        
        default_config = {
            'MAIL_SERVER': '',           # 默认SMTP服务器
            'MAIL_PORT': 465,            # 默认端口
            'MAIL_USERNAME': '',         # 默认用户名为空
            'MAIL_PASSWORD': '',         # 默认密码为空
            'MAIL_USE_SSL': True,        # 默认使用SSL
            'MAIL_USE_TLS': False        # 默认不使用TLS
        }
        
        # 如果SMTP_CONFIG是空字典, 初始化它, 否则, 确保所有默认键都存在
        if not SMTP_CONFIG:
            SMTP_CONFIG.update(default_config)
        else:
            for key, default_value in default_config.items():
                if key not in SMTP_CONFIG:
                    SMTP_CONFIG[key] = default_value
        
        # 获取用户名用于构建默认发送者
        if "smtp" in config and "SMTP_CONFIG" in config["smtp"]:
            smtp_config = config["smtp"]["SMTP_CONFIG"]
            
            # 更新每个配置项，但保留默认值
            for key, value in smtp_config.items():
                if key in SMTP_CONFIG:
                    SMTP_CONFIG[key] = value
            
            # 获取用户名用于构建默认发送者
            default_username = smtp_config.get('MAIL_USERNAME', '')
        else:
            # 如果没有配置SMTP_CONFIG，使用默认用户名
            default_username = SMTP_CONFIG.get('MAIL_USERNAME', '')
        SMTP_CONFIG['MAIL_DEFAULT_SENDER'] = (MAIL_SENDER_NAME, default_username)
        
    except Exception as e:
        logging.error(f"加载配置文件失败: {e}")
