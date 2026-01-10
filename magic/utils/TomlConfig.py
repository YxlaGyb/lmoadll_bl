# -*- coding: utf-8 -*-
#lmoadll_bl platform
#
#@copyright  Copyright (c) 2025 lmoadll_bl team
#@license  GNU General Public License 3.0
"""用于处理 TOML 配置文件的读取和写入操作"""
import os
import tomllib
import pathlib
from tomli_w import dump


CONFIG_PATH = pathlib.Path(__file__).parent.parent.parent / "config.toml"


__all__ = [
    "check_config_file",
    "DoesitexistConfigToml",
    "WriteConfigToml"
]

config_path = "config.toml"



def check_config_file():
    """检查config.toml是否存在, 如果不存在则创建默认配置"""
    if not CONFIG_PATH.exists():
        default_config = {
            "server": {
                "install": False
            }
        }
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_PATH, "wb") as f:
            dump(default_config, f)


def DoesitexistConfigToml(a:str, b:str) -> str | int | bool:
    """检查配置文件是否存在并读取"""
    if not os.path.exists(config_path):
        return False
    else:
        with open(config_path, "rb") as f:
            config: dict[str, dict[str, str | int | bool]] = tomllib.load(f)

        if not config[a][b]:
            return False
        else:
            return config[a][b]


def WriteConfigToml(a: str, b: str, c: str | int | bool) -> None:
    """检查键并写入配置文件"""
    # 检查配置文件是否存在, 不存在则创建新的配置文件和配置项
    if not os.path.exists(config_path):
        config = {a: {b: c}}
        with open(config_path, "wb") as f:
            dump(config, f)
        return

    # 读取现有配置文件
    with open(config_path, "rb") as f:
        config = tomllib.load(f)

    # 确保部分a存在
    if a not in config:
        config[a] = {}

    # 设置配置值
    config[a][b] = c

    with open(config_path, "wb") as f:
        dump(config, f)
