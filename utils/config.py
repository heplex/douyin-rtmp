# 版本信息
VERSION = "v1.0.4"

# GitHub 相关配置
GITHUB_CONFIG = {
    "REPO_OWNER": "heplex",
    "REPO_NAME": "douyin-rtmp",
    "API_URL": "https://gh-proxy.protoniot.com/api/repos/heplex/douyin-rtmp/releases/latest",
    "RELEASE_URL": "https://github.com/heplex/douyin-rtmp/releases/latest",
    "DOWNLOAD_URL": "https://gh-proxy.protoniot.com/heplex/douyin-rtmp/releases/latest/download/douyin-rtmp.exe",
    "REPO_URL": "https://github.com/heplex/douyin-rtmp",
}

import os
import json
from typing import Tuple


def load_obs_config() -> Tuple[str, bool, bool]:
    """
    加载OBS配置

    Returns:
        Tuple[str, bool, bool]: (obs路径, obs是否已配置, 推流配置是否已配置)
    """
    config_file = os.path.expanduser("~/.douyin-rtmp/config.json")
    obs_path = ""
    obs_configured = False
    stream_configured = False

    if os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
                obs_path = config.get("obs_path", "")
                if obs_path and os.path.exists(obs_path):
                    obs_configured = True

                # 加载推流配置路径
                stream_config_path = config.get("stream_config_path", "")
                if stream_config_path and os.path.exists(stream_config_path):
                    stream_configured = True

        except Exception:
            pass

    return obs_path, obs_configured, stream_configured

def set_config(key: str, value: any) -> bool:
    """
    设置配置参数

    Args:
        key (str): 配置键名
        value (any): 配置值

    Returns:
        bool: 设置是否成功
    """
    config_file = os.path.expanduser("~/.douyin-rtmp/config.json")
    config = {}
    
    # 确保配置目录存在
    os.makedirs(os.path.dirname(config_file), exist_ok=True)
    
    # 如果配置文件存在，先读取现有配置
    if os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception:
            return False
    
    # 更新或添加新配置
    config[key] = value
    
    # 保存配置
    try:
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
        return True
    except Exception:
        return False

def get_config(key: str) -> any:
    """
    获取配置参数

    Args:
        key (str): 配置键名

    Returns:
        any: 配置值，如果不存在返回 None
    """
    config_file = os.path.expanduser("~/.douyin-rtmp/config.json")
    
    if os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
                return config.get(key)
        except Exception:
            return None
    
    return None
