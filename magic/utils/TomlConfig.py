# -*- coding: utf-8 -*-
#lmoadll_bl platform
#
#@copyright  Copyright (c) 2025 lmoadll_bl team
#@license  GNU General Public License 3.0
"""用于处理 TOML 配置文件的读取和写入操作"""
import tomllib
import pathlib
from tomli_w import dump
from typing import Union, Dict


CONFIG_PATH = pathlib.Path(__file__).parent.parent.parent / "config.toml"
GLOBAL_CONFIG: Dict[str, Dict[str, Union[str, int, bool]]] = {}


__all__ = [
    "check_config_file",
    "DoesitexistConfigToml",
    "WriteConfigToml",
    "load_global_config",
    "GLOBAL_CONFIG"
]

config_path = "config.toml"



def check_config_file():
    """检查config.toml是否存在, 如果不存在则创建默认配置"""
    default_config = {
        "server": {
            "install": False
        }
    }
    if not CONFIG_PATH.exists():
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "wb") as f:
        dump(default_config, f)
    load_global_config()


def load_global_config() -> None:
    """加载config.toml文件内容到全局变量GLOBAL_CONFIG"""
    global GLOBAL_CONFIG
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "rb") as f:
            GLOBAL_CONFIG.update(tomllib.load(f))
    else:
        check_config_file() # 如果文件不存在，则创建并加载


def DoesitexistConfigToml(a: str, b: str):
    """检查配置文件是否存在并读取"""
    if not GLOBAL_CONFIG:
        load_global_config()

    if a in GLOBAL_CONFIG and b in GLOBAL_CONFIG[a]:
        return GLOBAL_CONFIG[a][b]
    return False


def WriteConfigToml(a: str, b: str, c: Union[str, int, bool]) -> None:
    """检查键并写入配置文件"""
    # 确保全局配置已加载
    if not GLOBAL_CONFIG:
        load_global_config()

    # 检查配置文件是否存在, 不存在则创建新的配置文件和配置项
    if not CONFIG_PATH.exists():
        config = {a: {b: c}}
        with open(CONFIG_PATH, "wb") as f:
            dump(config, f)
        GLOBAL_CONFIG.update(config) # 更新全局配置
        return

    # 读取现有配置文件
    with open(CONFIG_PATH, "rb") as f:
        config = tomllib.load(f)

    if a not in config:
        config[a] = {}

    config[a][b] = c

    with open(CONFIG_PATH, "wb") as f:
        dump(config, f)
    
    # 更新全局配置
    if a not in GLOBAL_CONFIG:
        GLOBAL_CONFIG[a] = {}
    GLOBAL_CONFIG[a][b] = c
