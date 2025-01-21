import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import os
import json
from utils.config import load_obs_config
from utils.content_config import OBS_HELP_TEXT


class OBSPanel:
    def __init__(self, parent, main_frame, logger):
        self.parent = parent
        self.main_frame = main_frame
        self.logger = logger

        # 状态变量
        self.obs_path = tk.StringVar()
        self.obs_status = tk.StringVar(value="未配置")
        self.stream_config_status = tk.StringVar(value="未配置")

        # 加载OBS配置
        obs_path, obs_configured, stream_configured = load_obs_config()
        self.obs_path.set(obs_path)
        self.obs_status.set("已配置" if obs_configured else "未配置")
        self.stream_config_status.set("已配置" if stream_configured else "未配置")

        # 初始化OBS工具类
        from utils.obs import OBSUtils

        self.obs_utils = OBSUtils()
        self.obs_utils.set_logger(self.logger)

        # 添加自动初始化
        self.auto_initialize()

        self.create_widgets()

    def create_widgets(self):
        # 添加OBS管理面板
        obs_frame = ttk.LabelFrame(self.main_frame, text="OBS管理", padding="5")
        obs_frame.grid(row=0, column=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5, padx=5)
        obs_frame.columnconfigure(1, weight=1)

        # 状态显示框架
        status_frame = ttk.Frame(obs_frame)
        status_frame.grid(row=0, column=0, columnspan=2, pady=5)

        ttk.Label(status_frame, text="OBS状态:", width=8).pack(side=tk.LEFT, padx=2)
        ttk.Label(status_frame, textvariable=self.obs_status, width=6).pack(
            side=tk.LEFT, padx=1
        )
        ttk.Label(status_frame, text="推流配置:", width=8).pack(side=tk.LEFT, padx=2)
        ttk.Label(status_frame, textvariable=self.stream_config_status, width=6).pack(
            side=tk.LEFT, padx=1
        )

        # OBS按钮组1
        obs_btn_frame1 = ttk.Frame(obs_frame)
        obs_btn_frame1.grid(row=1, column=0, columnspan=2, pady=(5, 2))
        ttk.Button(
            obs_btn_frame1,
            text="OBS路径配置",
            command=self.configure_obs_path,
            width=12,
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            obs_btn_frame1, text="推流配置", command=self.configure_stream, width=12
        ).pack(side=tk.LEFT, padx=5)

        # OBS按钮组2
        obs_btn_frame2 = ttk.Frame(obs_frame)
        obs_btn_frame2.grid(row=2, column=0, columnspan=2, pady=(5, 2))
        ttk.Button(
            obs_btn_frame2, text="同步推流码", command=self.sync_stream_config, width=12
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            obs_btn_frame2, text="启动OBS", command=self.launch_obs, width=12
        ).pack(side=tk.LEFT, padx=5)

        # OBS按钮组3
        obs_btn_frame3 = ttk.Frame(obs_frame)
        obs_btn_frame3.grid(row=3, column=0, columnspan=2, pady=(5, 2))
        ttk.Button(
            obs_btn_frame3, text="插件管理", command=self.open_plugin_manager, width=12
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            obs_btn_frame3, text="使用说明", command=self.show_obs_help, width=12
        ).pack(side=tk.LEFT, padx=5)

    # 这里添加所有OBS相关的方法
    def configure_obs_path(self):
        """配置OBS路径"""
        file_path = filedialog.askopenfilename(
            title="选择obs64.exe",
            filetypes=[("EXE files", "obs64.exe")],
            initialfile="obs64.exe",
        )

        if file_path:
            # 保存配置
            config_dir = os.path.expanduser("~/.douyin-rtmp")
            os.makedirs(config_dir, exist_ok=True)
            config_file = os.path.join(config_dir, "config.json")

            config = {}
            if os.path.exists(config_file):
                with open(config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)

            config["obs_path"] = file_path

            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)

            self.obs_path.set(file_path)
            self.obs_status.set("已配置")
            self.logger.info(f"OBS路径已配置: {file_path}")

    def launch_obs(self):
        """启动OBS"""
        success = self.obs_utils.launch_obs(
            sync_stream_config_callback=self.sync_stream_config
        )
        if success:
            self.logger.info("OBS启动成功")

    def show_obs_help(self):
        """显示OBS管理面板使用说明"""
        # 创建说明窗口
        help_window = tk.Toplevel()
        help_window.title("OBS管理使用说明")
        help_window.geometry("500x400")
        help_window.resizable(False, False)

        # 添加文本区域
        text_area = scrolledtext.ScrolledText(
            help_window, wrap=tk.WORD, width=50, height=20, padx=10, pady=10
        )
        text_area.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        text_area.insert(tk.END, OBS_HELP_TEXT)
        text_area.configure(state="disabled")  # 设置为只读

        # 窗口居中
        help_window.update_idletasks()
        width = help_window.winfo_width()
        height = help_window.winfo_height()
        x = (help_window.winfo_screenwidth() // 2) - (width // 2)
        y = (help_window.winfo_screenheight() // 2) - (height // 2)
        help_window.geometry(f"+{x}+{y}")

    def sync_stream_config(self, from_launch_button=False):
        """同步推流配置到OBS"""
        server_url = self.parent.server_address.get()
        stream_key = self.parent.stream_code.get()
        return self.obs_utils.sync_stream_config(
            server_url, stream_key, from_launch_button
        )

    def open_plugin_manager(self):
        """打开插件管理窗口"""
        from gui.plugin_manager import PluginManagerFrame

        # 创建新窗口
        plugin_window = tk.Toplevel(self.parent.root)
        plugin_window.title("插件管理")
        plugin_window.geometry("400x300")

        # 使窗口模态
        plugin_window.transient(self.parent.root)
        plugin_window.grab_set()

        # 添加插件管理界面
        plugin_frame = PluginManagerFrame(plugin_window)
        plugin_frame.pack(fill=tk.BOTH, expand=True)

        # 使窗口在屏幕中居中
        plugin_window.update_idletasks()
        width = plugin_window.winfo_width()
        height = plugin_window.winfo_height()
        x = (plugin_window.winfo_screenwidth() // 2) - (width // 2)
        y = (plugin_window.winfo_screenheight() // 2) - (height // 2)
        plugin_window.geometry("{}x{}+{}+{}".format(width, height, x, y))

    def configure_stream(self):
        """配置推流设置"""
        # 获取OBS配置文件夹路径
        profiles_path = os.path.expanduser(
            "~\\AppData\\Roaming\\obs-studio\\basic\\profiles"
        )

        if not os.path.exists(profiles_path):
            messagebox.showerror("错误", "未找到OBS配置文件夹，请确保已安装OBS并运行过")
            return

        file_path = filedialog.askopenfilename(
            title="选择service.json文件",
            initialdir=profiles_path,
            filetypes=[("JSON files", "service.json")],
            initialfile="service.json",
        )

        if file_path:
            if os.path.basename(file_path) != "service.json":
                messagebox.showerror("错误", "请选择service.json文件")
                return

            # 更新状态
            self.stream_config_status.set("已配置")
            self.logger.info(f"推流配置已选择: {file_path}")

            # 保存配置文件路径
            self.save_stream_config_path(file_path)

    def save_stream_config_path(self, file_path):
        """保存推流配置路径到配置文件"""
        config_dir = os.path.expanduser("~/.douyin-rtmp")
        config_file = os.path.join(config_dir, "config.json")

        config = {}
        if os.path.exists(config_file):
            with open(config_file, "r", encoding="utf-8") as f:
                config = json.load(f)

        config["stream_config_path"] = file_path

        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

    def auto_initialize(self):
        """自动初始化OBS配置"""
        if self.obs_status.get() == "未配置":
            obs_found = False
            # 首先尝试从注册表获取路径
            try:
                import winreg
                registry_paths = [
                    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\OBS Studio"),
                    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\OBS Studio"),
                    (winreg.HKEY_CURRENT_USER, r"SOFTWARE\OBS Studio"),
                    (winreg.HKEY_CURRENT_USER, r"SOFTWARE\WOW6432Node\OBS Studio"),
                    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\OBS Studio"),
                    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Classes\OBS.Studio"),
                ]

                for hkey, reg_path in registry_paths:
                    try:
                        with winreg.OpenKey(hkey, reg_path) as key:
                            install_path = winreg.QueryValue(key, None)
                            if not install_path:
                                for value_name in ["InstallLocation", "Path", "InstallPath"]:
                                    try:
                                        install_path = winreg.QueryValueEx(key, value_name)[0]
                                        break
                                    except WindowsError:
                                        continue

                            if install_path:
                                obs_exe_path = os.path.join(install_path, "bin", "64bit", "obs64.exe")
                                if os.path.exists(obs_exe_path):
                                    self.obs_path.set(obs_exe_path)
                                    self.obs_status.set("已配置")
                                    self.save_obs_path(obs_exe_path)
                                    self.logger.info(f"从注册表找到OBS路径: {obs_exe_path}，已进行自动配置")
                                    obs_found = True
                                    break
                    except WindowsError:
                        continue

            except Exception as e:
                self.logger.info(f"从注册表获取OBS路径失败: {str(e)}")

            # 如果从注册表没有找到，尝试Steam安装路径
            if not obs_found:
                try:
                    import winreg
                    # 检查两种可能的Steam注册表路径
                    steam_paths = []
                    
                    # 检查管理员安装路径 (HKEY_LOCAL_MACHINE)
                    try:
                        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam") as key:
                            steam_paths.append(winreg.QueryValueEx(key, "InstallPath")[0])
                    except WindowsError:
                        pass
                    
                    # 检查当前用户安装路径 (HKEY_CURRENT_USER)
                    try:
                        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Valve\Steam") as key:
                            steam_paths.append(winreg.QueryValueEx(key, "SteamPath")[0])
                    except WindowsError:
                        pass
                    
                    # 移除重复路径
                    steam_paths = list(set(steam_paths))
                    
                    # 对每个Steam安装路径进行检查
                    for steam_path in steam_paths:
                        # Steam库文件夹可能的位置
                        library_folders = [steam_path]
                        
                        # 检查新版本的库文件夹配置文件
                        new_library_file = os.path.join(steam_path, "config", "libraryfolders.vdf")
                        # 检查旧版本的库文件夹配置文件
                        old_library_file = os.path.join(steam_path, "steamapps", "libraryfolders.vdf")
                        
                        for library_file in [new_library_file, old_library_file]:
                            if os.path.exists(library_file):
                                with open(library_file, 'r', encoding='utf-8') as f:
                                    content = f.read()
                                    # 使用更完善的正则表达式匹配路径
                                    import re
                                    # 匹配新版Steam库文件格式
                                    paths = re.findall(r'"path"\s+"([^"]+)"', content)
                                    if not paths:
                                        # 匹配旧版Steam库文件格式
                                        paths = re.findall(r'"[0-9]+"\s+"([^"]+)"', content)
                                    library_folders.extend(paths)
                        
                        # 移除重复路径并规范化路径格式
                        library_folders = list(set([os.path.normpath(path.replace("\\\\", "\\")) for path in library_folders]))
                        
                        # 在所有Steam库中查找OBS
                        for library in library_folders:
                            # 可能的文件夹名称
                            possible_paths = [
                                os.path.join(library, "steamapps", "common", "OBS Studio", "bin", "64bit", "obs64.exe")
                            ]
                            
                            for obs_path in possible_paths:
                                if os.path.exists(obs_path):
                                    self.obs_path.set(obs_path)
                                    self.obs_status.set("已配置")
                                    self.save_obs_path(obs_path)
                                    self.logger.info(f"从Steam安装路径找到OBS: {obs_path}")
                                    obs_found = True
                                    break
                            
                            if obs_found:
                                break
                            
                except Exception as e:
                    self.logger.info(f"从Steam路径查找OBS失败: {str(e)}")

            # 如果从Steam没有找到，继续尝试常用路径
            if not obs_found:
                common_paths = [
                    "C:\\Program Files\\obs-studio\\bin\\64bit\\obs64.exe",
                    "D:\\Program Files\\obs-studio\\bin\\64bit\\obs64.exe",
                    "E:\\Program Files\\obs-studio\\bin\\64bit\\obs64.exe",
                    "F:\\Program Files\\obs-studio\\bin\\64bit\\obs64.exe",
                ]
                for path in common_paths:
                    if os.path.exists(path):
                        self.obs_path.set(path)
                        self.obs_status.set("已配置")
                        self.save_obs_path(path)
                        self.logger.info(f"自动找到OBS路径: {path}")
                        obs_found = True
                        break

                if not obs_found:
                    self.logger.info("未能自动找到OBS安装路径，请点击「OBS路径配置」按钮手动选择obs64.exe的位置")

        # 只有在OBS路径已配置的情况下才进行推流配置
        if (
            self.obs_status.get() == "已配置"
            and self.stream_config_status.get() == "未配置"
        ):
            profiles_path = os.path.expanduser(
                "~\\AppData\\Roaming\\obs-studio\\basic\\profiles"
            )
            if os.path.exists(profiles_path):
                # 首先检查"未命名"文件夹
                unnamed_path = os.path.join(profiles_path, "未命名")
                service_json_path = os.path.join(unnamed_path, "service.json")

                if os.path.exists(service_json_path):
                    self.save_stream_config_path(service_json_path)
                    self.stream_config_status.set("已配置")
                    self.logger.info(f"找到默认推流配置: {service_json_path}，已进行自动配置")
                    return

                # 遍历所有文件夹查找service.json
                for folder in os.listdir(profiles_path):
                    folder_path = os.path.join(profiles_path, folder)
                    if os.path.isdir(folder_path):
                        service_json_path = os.path.join(folder_path, "service.json")
                        if os.path.exists(service_json_path):
                            self.save_stream_config_path(service_json_path)
                            self.stream_config_status.set("已配置")
                            self.logger.info(f"找到推流配置: {service_json_path}")
                            return

                # 如果没有找到任何配置，在"未命名"文件夹下创建新的配置
                os.makedirs(unnamed_path, exist_ok=True)
                service_json_path = os.path.join(unnamed_path, "service.json")
                default_config = {
                    "settings": {
                        "bwtest": False,
                        "key": "",
                        "server": "",
                        "service": "rtmp",
                    },
                    "type": "rtmp_custom",
                }
                with open(service_json_path, "w", encoding="utf-8") as f:
                    json.dump(default_config, f, indent=4)

                self.save_stream_config_path(service_json_path)
                self.stream_config_status.set("已配置")
                self.logger.info(f"创建新的推流配置: {service_json_path}")

    def save_obs_path(self, file_path):
        """保存OBS路径到配置文件"""
        config_dir = os.path.expanduser("~/.douyin-rtmp")
        os.makedirs(config_dir, exist_ok=True)
        config_file = os.path.join(config_dir, "config.json")

        config = {}
        if os.path.exists(config_file):
            with open(config_file, "r", encoding="utf-8") as f:
                config = json.load(f)

        config["obs_path"] = file_path

        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
