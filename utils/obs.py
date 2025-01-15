import os
import json
import requests
import zipfile
from pathlib import Path
from tkinter import messagebox
from utils.config import load_obs_config


class OBSUtils:
    def __init__(self):
        pass

    def get_obs_path(self):
        """获取OBS安装路径"""
        obs_path, _, _ = load_obs_config()
        return obs_path if obs_path else None

    def is_obs_configured(self):
        """检查是否配置了OBS路径"""
        _, obs_configured, _ = load_obs_config()
        return obs_configured

    def get_plugin_install_path(self):
        """获取插件安装路径（OBS根目录）"""
        obs_path = self.get_obs_path()
        if not obs_path:
            return None
        # 从 bin/64bit/obs64.exe 回退两级到 OBS 根目录
        return str(Path(obs_path).parent.parent.parent)

    def check_plugin_status(self, install_name):
        """检查插件安装状态"""
        install_path = self.get_plugin_install_path()
        if not install_path:
            return "未知"

        # 检查插件文件是否存在
        plugin_path = os.path.join(
            install_path, "obs-plugins", "64bit", f"{install_name}.dll"
        )
        return "已安装" if os.path.exists(plugin_path) else "未安装"

    def install_plugin(self, plugin_config):
        """安装插件"""
        if not self.is_obs_configured():
            messagebox.showerror("错误", "请先配置OBS路径！")
            return False

        if plugin_config.get("installType") == "1":
            try:
                # 获取最新版本信息
                latest_release = self._get_latest_release(plugin_config["releaseUrl"])
                if not latest_release:
                    return False

                # 下载并安装插件
                success = self._download_and_install(latest_release, plugin_config)
                if success:
                    messagebox.showinfo(
                        "成功", f"{plugin_config['pluginName']} 安装成功！"
                    )
                    return True
            except Exception as e:
                messagebox.showerror("错误", f"安装失败：{str(e)}")
                return False
        return False

    def _get_latest_release(self, release_url):
        """获取最新版本信息"""
        parts = release_url.split("/")
        if len(parts) >= 5:
            owner = parts[3]
            repo = parts[4]
            api_url = f"https://gh-proxy.protoniot.com/api/repos/{owner}/{repo}/releases/latest"

            response = requests.get(api_url)
            if response.status_code == 200:
                return response.json()
            else:
                messagebox.showerror("错误", "获取最新版本信息失败！")
        return None

    def _download_and_install(self, release_info, plugin_config, progress_callback=None):
        """下载并安装插件"""
        suffix = plugin_config["suffix"]

        # 查找匹配后缀的资源
        target_asset = None
        for asset in release_info["assets"]:
            if asset["name"].endswith(suffix):
                target_asset = asset
                break

        if not target_asset:
            messagebox.showerror("错误", f"未找到后缀为 {suffix} 的安装文件！")
            return False

        # 下载文件
        download_url = target_asset["browser_download_url"]
        response = requests.get(download_url, stream=True)

        if response.status_code != 200:
            messagebox.showerror("错误", "下载文件失败！")
            return False

        # 获取文件总大小
        total_size = int(response.headers.get('content-length', 0))
        
        # 保存文件
        download_path = os.path.join("downloads", target_asset["name"])
        os.makedirs("downloads", exist_ok=True)

        block_size = 8192
        downloaded_size = 0

        with open(download_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=block_size):
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)
                    # 计算下载进度
                    progress = (downloaded_size / total_size) * 100 if total_size else 0
                    # 调用回调函数更新进度
                    if progress_callback:
                        progress_callback(progress)

        # 如果是zip文件，解压到OBS目录
        if suffix == "zip":
            try:
                install_path = self.get_plugin_install_path()
                if not install_path:
                    messagebox.showerror("错误", "无法获取插件安装路径！")
                    return False

                with zipfile.ZipFile(download_path, "r") as zip_ref:
                    zip_ref.extractall(install_path)

                # 删除下载的zip文件
                os.remove(download_path)
                return True
            except Exception as e:
                messagebox.showerror("错误", f"解压文件失败：{str(e)}")
                return False

        return True

    def uninstall_plugin(self, plugin_config):
        """
        卸载OBS插件

        Args:
            plugin_config (dict): 插件配置信息

        Returns:
            bool: 卸载是否成功
        """
        try:
            if plugin_config.get("suffix") == "zip":
                import os
                import glob
                import shutil

                # 获取OBS安装路径
                obs_root = self.get_plugin_install_path()
                if not obs_root:
                    return False

                # 删除data/obs-plugins下的文件夹
                data_plugin_path = os.path.join(
                    obs_root, "data", "obs-plugins", plugin_config["installName"]
                )
                if os.path.exists(data_plugin_path):
                    shutil.rmtree(data_plugin_path)

                # 删除obs-plugins/64bit下的相关文件
                bin_plugin_path = os.path.join(obs_root, "obs-plugins", "64bit")
                plugin_files = glob.glob(
                    os.path.join(bin_plugin_path, f"{plugin_config['installName']}.*")
                )
                for file in plugin_files:
                    if os.path.exists(file):
                        os.remove(file)

                return True

        except Exception as e:
            return False
