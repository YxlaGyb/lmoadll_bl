# -*- coding: utf-8 -*-
import logging
import os
import re
import zipfile
import datetime
from pathlib import Path
import colorlog

# --- 配置与常量 ---
LOG_DIR = Path(__file__).parents[2] / 'contents' / 'logs'
LEVEL_MAP = {'DEBUG': 'DBG', 'INFO': 'INF', 'WARNING': 'WRN', 'ERROR': 'ERR', 'CRITICAL': 'CRT'}
COLOR_CONFIG = {'DBG': 'cyan', 'INF': 'green', 'WRN': 'yellow', 'ERR': 'red', 'CRT': 'bold_red'}

class AbbreviatedFormatter(colorlog.ColoredFormatter):
    """缩写级别并支持颜色"""
    def format(self, record):
        record.levelname = LEVEL_MAP.get(record.levelname, record.levelname[:3])
        return super().format(record)

class LogManager:
    @staticmethod
    def setup_dir():
        LOG_DIR.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def archive_old(current_date: str):
        """归档非当天的日志"""
        files_by_date = {}
        for f in LOG_DIR.glob("*.log"):
            date_part = "-".join(f.stem.split("-")[:3])
            if date_part != current_date:
                files_by_date.setdefault(date_part, []).append(f)

        for date_str, files in files_by_date.items():
            zip_path = LOG_DIR / f"{date_str}-logs.zip"
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for f in files:
                    zipf.write(f, f.name)
                    f.unlink()
            print(f"Archived {len(files)} logs to {zip_path.name}")

    @staticmethod
    def get_current_path() -> Path:
        """获取今日最新的日志路径"""
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
            existing = sorted(LOG_DIR.glob(f"{today}-*.log"))
            if existing: 
                return existing[-1]

        LogManager.archive_old(today)
        counts = [int(f.stem.split('-')[-1]) for f in LOG_DIR.glob(f"{today}-*.log") if f.stem.split('-')[-1].isdigit()]
        new_count = max(counts, default=0) + 1
        return LOG_DIR / f"{today}-{new_count}.log"

def init_logger():
    LogManager.setup_dir()
    log_path = LogManager.get_current_path()
    
    logger = colorlog.getLogger()
    if logger.handlers: 
        return logger # 避免重复初始化
    
    logger.setLevel(logging.DEBUG)

    console_hdl = colorlog.StreamHandler()
    console_hdl.setFormatter(AbbreviatedFormatter(
        fmt='%(log_color)s[%(asctime)s %(levelname)s]%(reset)s: %(message)s',
        datefmt='%H:%M:%S',
        log_colors=COLOR_CONFIG
    ))

    file_hdl = logging.FileHandler(log_path, encoding='utf-8')
    file_hdl.setFormatter(logging.Formatter('[%(asctime)s %(levelname)s]: %(message)s', '%Y-%m-%d %H:%M:%S'))
    ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
    file_hdl.addFilter(lambda record: setattr(record, 'msg', ansi_escape.sub('', str(record.msg))) or True)

    logger.addHandler(console_hdl)
    logger.addHandler(file_hdl)
    logger.info(f"Log initialized: {log_path.name}")
    return logger

# 全局实例
logger = init_logger()
