import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import webbrowser
import sys
from scapy.arch.windows import get_windows_if_list
from core.npcap import NpcapManager
from utils.logger import Logger
from utils.network import NetworkInterface
from gui.widgets import (
    create_log_panel,
    create_help_dialog,
    create_disclaimer_dialog,
    create_about_dialog,
)
from utils.config import VERSION, GITHUB_CONFIG
import threading
from utils.version import check_for_updates
from gui.ads import AdPanel
from gui.obs import OBSPanel
from gui.control import ControlPanel
from utils.resource import resource_path


class StreamCaptureGUI:
    def __init__(self, root):
        self.root = root
        self.root.title(f"抖音直播推流地址获取工具 {VERSION}")
        self.root.geometry("800x600")

        # 设置窗口图标
        try:
            icon_path = resource_path("assets/logo.ico")
            self.root.iconbitmap(icon_path)
        except tk.TclError:
            print("无法加载图标文件")

        # 显示免责声明
        # self.show_disclaimer()

        # 创建主框架
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 设置网格权重
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=1)

        # 状态变量
        self.server_address = tk.StringVar()
        self.stream_code = tk.StringVar()

        # 初始化基础组件
        self.logger = Logger()
        self.network = NetworkInterface(self.logger)
        self.npcap = NpcapManager(self.logger)
        
        # 创建界面组件
        self.create_widgets()

        # 检查Npcap
        if not self.check_npcap():
            self.check_and_install_npcap()
            sys.exit(1)

        # 在窗口加载完成后检查更新
        self.root.after(1000, self.async_check_updates)

    def create_widgets(self):
        # 创建菜单栏
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # 工具菜单
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="工具", menu=tools_menu)
        tools_menu.add_command(label="安装 Npcap", command=self.install_npcap)
        tools_menu.add_command(label="卸载 Npcap", command=self.uninstall_npcap)

        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(
            label="GitHub 仓库",
            command=lambda: webbrowser.open(GITHUB_CONFIG["RELEASE_URL"]),
        )
        help_menu.add_separator()
        help_menu.add_command(label=f"关于 ({VERSION})", command=self.show_about)

        # 主布局使用网格
        self.main_frame.columnconfigure(1, weight=1)

        # 创建控制面板
        self.control_panel = ControlPanel(self)

        # 创建日志面板并保存引用
        self.log_notebook = create_log_panel(self)  # 保存notebook的引用以供后续使用

        # 添加底栏
        self.create_status_bar()

        # 添加OBS管理面板
        self.obs_panel = OBSPanel(self, self.main_frame, self.logger)

        # 添加广告位面板
        self.ad_panel = AdPanel(parent=self.main_frame)

        # 在窗口加载完成后异步获取广告内容
        self.root.after(1000, self.ad_panel.async_fetch_ad_content)

    def create_status_bar(self):
        """创建底栏"""
        status_frame = ttk.Frame(self.main_frame)
        status_frame.grid(row=2, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5)

        # 左侧版本信息
        ttk.Label(status_frame, text=f"版本: {VERSION}").pack(side=tk.LEFT, padx=5)

        # 右侧按钮组
        buttons_frame = ttk.Frame(status_frame)
        buttons_frame.pack(side=tk.RIGHT)

        # 打赏按钮
        ttk.Button(
            buttons_frame, text="请作者喝杯咖啡", command=self.show_donation, width=14
        ).pack(side=tk.LEFT, padx=5)

        # 免责声明按钮
        ttk.Button(
            buttons_frame, text="免责声明", command=self.show_disclaimer, width=10
        ).pack(side=tk.LEFT, padx=5)

        # 使用说明按钮
        ttk.Button(
            buttons_frame, text="使用说明", command=self.show_help, width=10
        ).pack(side=tk.LEFT, padx=5)

    def show_donation(self):
        """显示打赏对话框"""
        from gui.widgets import create_donation_dialog

        create_donation_dialog(self.root, self.logger, resource_path)

    def log_to_console(self, message):
        """输出日志到控制台"""
        self.logger.info(message)

    def clear_console(self):
        """清除控制台内容"""
        self.logger.clear_console()

    def check_npcap(self):
        """检查Npcap是否已安装"""
        return self.npcap.check()

    def check_and_install_npcap(self):
        """检查并安装Npcap"""
        return self.npcap.check_and_install()

    def uninstall_npcap(self):
        """卸载Npcap"""
        self.npcap.uninstall_npcap()

    def async_check_updates(self):
        """异步检查更新"""
        thread = threading.Thread(target=check_for_updates)
        thread.daemon = True  # 设置为守护线程，这样主程序退出时线程会自动结束
        thread.start()

    def install_npcap(self):
        """手动安装 Npcap"""
        try:
            # 使用 NpcapManager 的方法进行安装
            if not self.npcap.check():
                self.npcap.install_npcap()
            else:
                messagebox.showinfo("提示", "Npcap 已经安装")

        except Exception as e:
            error_msg = f"启动 Npcap 安装程序失败: {str(e)}"
            self.logger.error(error_msg)
            messagebox.showerror("错误", error_msg)

    def show_help(self):
        """显示使用说明弹窗"""
        create_help_dialog(self.root)

    def show_disclaimer(self):
        """显示免责声明弹窗"""
        create_disclaimer_dialog(self.root)

    def show_about(self):
        """显示关于对话框"""
        create_about_dialog(self.root, VERSION)

    def clear_logs(self):
        """清除所有日志"""
        self.logger.clear_console()
        self.logger.clear_packet_console()

    def clear_packet_console(self):
        """清除数据包控制台内容"""
        self.logger.clear_packet_console()
        self.logger.info("数据包日志已清除")  # 在主控制台显示清除提示

    def log_packet(self, message):
        """记录数据包信息到数据包控制台"""
        self.packet_console.insert(tk.END, f"{message}\n")
        self.packet_console.see(tk.END)

        # 如果发现关键数据包，自动切换到控制台标签
        if ">>> 发现" in message:
            self.log_notebook.select(1)  # 切换到数据包监控标签
