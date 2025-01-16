import os
import requests
import zipfile
from pathlib import Path
from tkinter import messagebox
from utils.config import load_obs_config
import tkinter as tk
from tkinter import ttk
import psutil


class OBSUtils:
    def __init__(self):
        self._installing = False
        self.logger = None  # 添加logger属性

    def set_logger(self, logger):
        """设置logger"""
        self.logger = logger

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

        # 创建进度条对话框
        progress_window = tk.Toplevel()
        progress_window.title("安装进度")
        progress_window.geometry("300x150")
        progress_window.transient(tk._default_root)
        progress_window.resizable(False, False)
        
        # 立即设置窗口位置到屏幕中央
        screen_width = progress_window.winfo_screenwidth()
        screen_height = progress_window.winfo_screenheight()
        window_width = 300
        window_height = 150
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        progress_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        progress_window.grab_set()

        # 添加标签和进度条
        label = ttk.Label(progress_window, text="正在准备下载...", font=("微软雅黑", 9))
        label.pack(pady=10)
        
        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(
            progress_window, 
            variable=progress_var,
            maximum=100,
            mode='determinate',
            length=200
        )
        progress_bar.pack(pady=10)
        
        percentage_label = ttk.Label(progress_window, text="0%", font=("微软雅黑", 9))
        percentage_label.pack(pady=5)
        
        # 立即更新窗口显示
        progress_window.update()

        try:
            # 更新标签文本
            label.config(text="正在连接服务器...")
            progress_window.update()
            
            # 开始下载
            response = requests.get(download_url, stream=True)
            if response.status_code != 200:
                messagebox.showerror("错误", "下载文件失败！")
                progress_window.destroy()
                return False

            # 获取文件大小
            total_size = int(response.headers.get('content-length', 0))
            
            # 更新标签文本
            label.config(text="正在下载插件...")
            progress_window.update()
            
            # 保存文件
            filename = f"{install_name}{suffix}"
            download_path = os.path.join("downloads", filename)
            os.makedirs("downloads", exist_ok=True)

            block_size = 1024  # 1 KB
            downloaded_size = 0

            with open(download_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=block_size):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        # 更新进度
                        if total_size:
                            progress = (downloaded_size / total_size) * 100
                            progress_var.set(progress)
                            percentage_label.config(text=f"{progress:.1f}%")
                            progress_window.update()

            # 如果是zip文件，解压到OBS目录
            if suffix == ".zip":
                label.config(text="正在解压文件...")
                progress_window.update()
                
                try:
                    install_path = self.get_plugin_install_path()
                    if not install_path:
                        messagebox.showerror("错误", "无法获取插件安装路径！")
                        progress_window.destroy()
                        return False

                    with zipfile.ZipFile(download_path, "r") as zip_ref:
                        zip_ref.extractall(install_path)

                    # 删除下载的zip文件
                    os.remove(download_path)
                    progress_window.destroy()
                    return True
                except Exception as e:
                    messagebox.showerror("错误", f"解压文件失败：{str(e)}")
                    progress_window.destroy()
                    return False

            # 删除下载的文件
            os.remove(download_path)
            progress_window.destroy()
            messagebox.showerror("错误", f"{suffix}后缀文件不支持安装")
            return False
            
        except Exception as e:
            progress_window.destroy()
            messagebox.showerror("错误", f"下载失败：{str(e)}")
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
            messagebox.showerror("错误", f"暂不支持{suffix}后缀文件卸载，请尝试在obs插件路径手动删除")
            return False
        except Exception as e:
            return False

    def is_obs_running(self):
        """检查OBS是否正在运行"""
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] and 'obs64.exe' in proc.info['name'].lower():
                return True
        return False

    def kill_obs_process(self):
        """结束OBS进程"""
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] and 'obs64.exe' in proc.info['name'].lower():
                proc.kill()

    def launch_obs(self, sync_stream_config_callback=None):
        """
        启动OBS
        
        Args:
            sync_stream_config_callback: 同步推流配置的回调函数
            
        Returns:
            bool: 启动是否成功
        """
        import os
        import subprocess
        
        obs_path = self.get_obs_path()
        
        if not obs_path:
            messagebox.showwarning("警告", "请先配置OBS路径")
            return False
            
        if not os.path.exists(obs_path):
            messagebox.showerror("错误", "配置的OBS路径不存在，请重新配置")
            return False
            
        # 如果提供了同步配置回调函数，则执行同步
        if sync_stream_config_callback:
            sync_success = sync_stream_config_callback(from_launch_button=True)
            if not sync_success:
                result = messagebox.askokcancel(
                    "提示", 
                    "推流配置同步失败，将使用原有配置启动OBS。\n是否继续？"
                )
                if not result:
                    return False
                    
        try:
            # 获取OBS安装目录
            obs_dir = os.path.dirname(obs_path)
            # 在OBS目录下启动程序
            subprocess.Popen([obs_path], cwd=obs_dir)
            return True
        except Exception as e:
            messagebox.showerror("错误", f"启动OBS失败: {str(e)}")
            return False

    def sync_stream_config(self, server_url, stream_key, from_launch_button=False):
        """
        同步推流配置到OBS
        
        Args:
            server_url (str): 推流服务器地址
            stream_key (str): 推流密钥
            from_launch_button (bool): 是否从启动按钮调用
            
        Returns:
            bool: 同步是否成功
        """
        import json
        import os
        from tkinter import messagebox

        # 检查推流配置文件
        config_file = os.path.expanduser("~/.douyin-rtmp/config.json")
        stream_config_path = None
        if os.path.exists(config_file):
            with open(config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
                stream_config_path = config.get("stream_config_path")

        if not stream_config_path or not os.path.exists(stream_config_path) or not server_url or not stream_key:
            messagebox.showwarning("警告", "请确保已配置OBS推流配置文件路径，并已成功捕获推流地址！")
            return False

        try:
            if self.logger:
                self.logger.info("\n正在同步推流配置...")

            # 创建标准格式的配置
            service_config = {
                "type": "rtmp_custom",
                "settings": {
                    "server": server_url,
                    "key": stream_key,
                    "use_auth": False,
                    "bwtest": False,
                },
            }

            # 保存更新后的配置
            with open(stream_config_path, "w", encoding="utf-8") as f:
                json.dump(service_config, f, indent=4)

            if self.logger:
                self.logger.info("推流配置同步成功")

            # 根据调用来源和OBS运行状态显示不同的提示
            if not from_launch_button:
                if self.is_obs_running():
                    result = messagebox.askokcancel(
                        "提示", 
                        "推流配置已同步。检测到OBS正在运行，需要重启OBS才能生效。\n是否立即重启OBS？如果OBS有弹窗，请选择正常运行。"
                    )
                    if result:
                        self.kill_obs_process()
                        self.launch_obs()
                else:
                    result = messagebox.askokcancel(
                        "提示", 
                        "推流配置已同步。是否立即启动OBS？"
                    )
                    if result:
                        self.launch_obs()

            return True

        except Exception as e:
            error_msg = f"同步推流配置失败: {str(e)}"
            if self.logger:
                self.logger.error(error_msg)
            messagebox.showerror("错误", error_msg)
            return False
