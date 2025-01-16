import os
import json
import requests
import zipfile
from pathlib import Path
from tkinter import messagebox
from utils.config import load_obs_config


class OBSUtils:
    def __init__(self):
        self._installing = False

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
        # 检查是否正在安装
        if self._installing:
            messagebox.showinfo("提示", "正在安装中，请稍候...")
            return False

        if not self.is_obs_configured():
            messagebox.showerror("错误", "请先配置OBS路径！")
            return False

        try:
            self._installing = True  # 设置安装状态为True
            # 继续文件下载
            success = self._download_and_install(
                plugin_config["downloadUrl"], plugin_config["installName"]
            )
            if success:
                messagebox.showinfo("成功", f"{plugin_config['pluginName']} 安装成功！")
                return True
        except Exception as e:
            messagebox.showerror("错误", f"安装失败：{str(e)}")
            return False
        finally:
            self._installing = False  # 无论成功失败都重置安装状态
        return False

    def _get_plugin_suffix(self, plugin_config):
        """获取插件文件后缀

        Args:
            plugin_config (dict): 插件配置信息

        Returns:
            str: 插件文件后缀（例如：'.zip'）
        """
        if "downloadUrl" in plugin_config:
            return Path(plugin_config["downloadUrl"]).suffix.lower()
        return plugin_config.get("suffix", "").lower()

    def _download_and_install(self, download_url, install_name):
        """下载并安装插件"""
        # 在方法内部获取后缀
        suffix = Path(download_url).suffix.lower()

        # 下载文件
        response = requests.get(download_url, stream=True)
        if response.status_code != 200:
            messagebox.showerror("错误", "下载文件失败！")
            return False

        # 保存文件
        filename = f"{install_name}{suffix}"
        download_path = os.path.join("downloads", filename)
        os.makedirs("downloads", exist_ok=True)

        with open(download_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        # 如果是zip文件，解压到OBS目录
        if suffix == ".zip":
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

        # 删除下载的zip文件
        os.remove(download_path)
        messagebox.showerror("错误", f"{suffix}后缀文件不支持安装")
        return False

    def uninstall_plugin(self, plugin_config):
        import os
        import glob
        import shutil

        """
        卸载OBS插件

        Args:
            plugin_config (dict): 插件配置信息

        Returns:
            bool: 卸载是否成功
        """
        try:
            suffix = self._get_plugin_suffix(plugin_config)
            if suffix == ".zip":
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
