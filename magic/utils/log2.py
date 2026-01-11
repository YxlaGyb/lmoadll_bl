# -*- coding: utf-8 -*-
#lmoadll_bl platform
#
#@copyright  Copyright (c) 2025 lmoadll_bl team
#@license  GNU General Public License 3.0
"""
日志配置模块
提供颜色日志格式化和缩写日志级别功能，以及日志文件保存功能
"""
import logging
import colorlog
import os
import datetime
import zipfile


class AbbreviatedColorFormatter(colorlog.ColoredFormatter):
    def format(self, record):
        level_abbr = {
            'DEBUG':    'DBG',
            'INFO':     'INF', 
            'WARNING':  'WRN',
            'ERROR':    'ERR',
            'CRITICAL': 'CRIT'
        }
        record.levelname = level_abbr.get(record.levelname, record.levelname)
        return super().format(record)


def get_log_directory():
    """获取日志目录路径"""
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    log_directory = os.path.join(project_root, 'contents', 'logs')
    os.makedirs(log_directory, exist_ok=True)
    return log_directory


def get_start_count():
    """获取启动次数(通过扫描目录中现有日志文件)"""
    log_dir = get_log_directory()
    current_date = datetime.datetime.now().strftime('%Y-%m-%d')
    count = 0
    try:
        for filename in os.listdir(log_dir):
            if filename.startswith(current_date) and filename.endswith('.log'):
                try:
                    parts = filename.split('-')
                    if len(parts) >= 3:
                        number_part = parts[-1].split('.')[0]
                        if number_part.isdigit():
                            file_count = int(number_part)
                            count = max(count, file_count)
                except Exception:
                    pass
    except Exception as e:
        print(f"扫描日志文件失败: {e}")
    return count + 1


def create_log_file():
    """创建日志文件"""
    log_dir = get_log_directory()
    current_date = datetime.datetime.now().strftime('%Y-%m-%d')
    start_count = get_start_count()
    log_filename = f"{current_date}-{start_count}.log"
    log_filepath = os.path.join(log_dir, log_filename)
    return log_filepath


def archive_old_logs():
    """打包旧日志文件"""
    log_dir = get_log_directory()
    current_date = datetime.datetime.now().strftime('%Y-%m-%d')
    date_groups = {}
    for filename in os.listdir(log_dir):
        if os.path.isfile(os.path.join(log_dir, filename)) and filename.endswith('.log'):
            try:
                # 文件名格式:2025-11-19-1.log
                date_part = '-'.join(filename.split('-')[:3])
                
                if date_part != current_date:
                    if date_part not in date_groups:
                        date_groups[date_part] = []
                    date_groups[date_part].append(filename)
            except Exception:
                continue
    
    # 为每个日期的日志文件创建zip包
    for date_str, files in date_groups.items():
        if len(files) > 0:
            zip_filename = f"{date_str}-logs.zip"
            zip_filepath = os.path.join(log_dir, zip_filename)
            if os.path.exists(zip_filepath):
                try:
                    os.remove(zip_filepath)
                except Exception as e:
                    print(f"删除旧zip文件失败: {e}")
                    continue
            try:
                with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for filename in files:
                        file_path = os.path.join(log_dir, filename)
                        zipf.write(file_path, filename)
                        # 打包后删除原文件
                        os.remove(file_path)
                print(f"已将{len(files)}个{date_str}的日志文件打包到{zip_filename}")
            except Exception as e:
                print(f"打包{date_str}的日志文件失败: {e}")


# 使用环境变量来跟踪是否已经初始化过日志系统
# 检查是否在Quart的重启过程中
_is_reload = os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
_configured_logger = None # 全局变量，用于存储已配置的logger


def init_logger():
    """初始化日志配置"""
    global _configured_logger
    
    # 如果已经配置过logger，直接返回
    if _configured_logger is not None:
        return _configured_logger
    
    # 在Quart调试模式下，只有主进程才创建新的日志文件
    # WERKZEUG_RUN_MAIN环境变量在Quart重启时为'true'
    if _is_reload:
        # 这是Quart的重启过程，使用现有的日志文件
        # 获取今天的日志文件列表，使用最新的一个
        log_dir = get_log_directory()
        current_date = datetime.datetime.now().strftime('%Y-%m-%d')
        
        # 查找今天的日志文件
        today_logs = []
        try:
            for filename in os.listdir(log_dir):
                if filename.startswith(current_date) and filename.endswith('.log'):
                    today_logs.append(filename)
        except Exception:
            today_logs = []
        
        if today_logs:
            # 使用最新的日志文件
            today_logs.sort()
            log_filepath = os.path.join(log_dir, today_logs[-1])
        else:
            log_filepath = create_log_file()
    else:
        archive_old_logs()
        log_filepath = create_log_file()
    
    # 设置logger
    logger = colorlog.getLogger()
    logger.setLevel(logging.DEBUG)
    
    # 清除已有的handler
    if logger.handlers:
        logger.handlers.clear()
    
    console_handler = colorlog.StreamHandler()
    console_handler.setFormatter(AbbreviatedColorFormatter(
        fmt='%(log_color)s[%(asctime)s %(levelname)s]%(reset)s: %(message)s',
        datefmt='%H:%M:%S',
        log_colors={
            'DBG':  'cyan',
            'INF':  'green',
            'WRN':  'yellow',
            'ERR':  'red',
            'CRIT': 'bold_red',
        }
    ))
    logger.addHandler(console_handler)
    
    # 添加文件handler
    file_handler = logging.FileHandler(log_filepath, encoding='utf-8')
    # 文件日志格式不包含颜色代码, 使用自定义过滤器去除颜色代码
    file_formatter = logging.Formatter(
        fmt='[%(asctime)s %(levelname)s]: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    
    # 添加过滤器去除颜色代码
    class NoColorFilter(logging.Filter):
        def filter(self, record):
            if hasattr(record, 'msg') and isinstance(record.msg, str):
                # 去除ANSI颜色代码
                import re
                ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
                record.msg = ansi_escape.sub('', record.msg)
            return True
    file_handler.addFilter(NoColorFilter())
    logger.addHandler(file_handler)
    logger.info(f"log file: {log_filepath}")
    _configured_logger = logger # 保存已配置的logger
    return logger

logger = init_logger()
