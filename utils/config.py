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
