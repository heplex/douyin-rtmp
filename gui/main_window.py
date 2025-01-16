import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import webbrowser
import os
import sys
import subprocess
from scapy.arch.windows import get_windows_if_list
from core.capture import PacketCapture
from core.npcap import NpcapManager
from utils.logger import Logger
from utils.network import NetworkInterface
from gui.widgets import create_control_panel, create_log_panel, create_help_panel
from utils.config import VERSION, GITHUB_CONFIG, load_obs_config
import threading
from utils.version import check_for_updates
from utils.content_config import (
    ADVERTISEMENT_TEXT,
    HELP_TEXT,
    OBS_HELP_TEXT,
)  # 更新导入语句
import psutil  # 需要添加此导入


def resource_path(relative_path):
    """获取资源文件的绝对路径，兼容开发、Nuitka打包和PyInstaller打包后的环境"""
    if hasattr(sys, "_MEIPASS"):
        # 在PyInstaller打包后的环境中
        base_path = sys._MEIPASS
    else:
        # 在Nuitka打包后的环境或开发环境中
        base_path = os.path.dirname(os.path.dirname(__file__))

    return os.path.join(base_path, relative_path)


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
        self.is_capturing = False
        self.server_address = tk.StringVar()
        self.stream_code = tk.StringVar()
        self.status_text = tk.StringVar(value="待开始")
        self.selected_interface = tk.StringVar()

        # 添加OBS相关变量
        self.obs_path = tk.StringVar()
        self.obs_status = tk.StringVar(value="未配置")
        self.stream_config_status = tk.StringVar(value="未配置")

        # 加载OBS配置
        obs_path, obs_configured, stream_configured = load_obs_config()
        self.obs_path.set(obs_path)
        self.obs_status.set("已配置" if obs_configured else "未配置")
        self.stream_config_status.set("已配置" if stream_configured else "未配置")

        # 初始化组件
        self.logger = Logger()
        self.network = NetworkInterface(self.logger)
        self.npcap = NpcapManager(self.logger)
        self.capture = PacketCapture(self.logger)

        # 设置回调函数
        self.capture.add_callback(self.on_capture_complete)

        # 创建界面组件
        self.create_widgets()

        # 加载网络接口
        self.load_interfaces()

        # 检查Npcap
        if not self.check_npcap():
            self.check_and_install_npcap()
            sys.exit(1)

        # 在窗口加载完成后检查更新
        self.root.after(1000, self.async_check_updates)

        # 初始化OBS工具类
        from utils.obs import OBSUtils
        self.obs_utils = OBSUtils()
        self.obs_utils.set_logger(self.logger)  # 设置logger

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

        # 创建标签页控件
        self.log_notebook = ttk.Notebook(self.main_frame)
        self.log_notebook.grid(
            row=1, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S)
        )
        self.main_frame.grid_rowconfigure(1, weight=1)

        # 创建数据包日志标签页
        packet_frame = ttk.Frame(self.log_notebook, padding="5")
        self.packet_console = scrolledtext.ScrolledText(
            packet_frame, wrap=tk.WORD, height=8
        )
        self.packet_console.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        packet_frame.grid_columnconfigure(0, weight=1)
        packet_frame.grid_rowconfigure(0, weight=1)

        # 数据包日志清除按钮
        ttk.Button(
            packet_frame,
            text="清除数据包日志",
            command=self.clear_packet_console,
            width=15,
        ).grid(row=1, column=0, pady=5)

        # 创建主控制台标签页
        console_frame = ttk.Frame(self.log_notebook, padding="5")
        self.console = scrolledtext.ScrolledText(console_frame, wrap=tk.WORD, height=8)
        self.console.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        console_frame.grid_columnconfigure(0, weight=1)
        console_frame.grid_rowconfigure(0, weight=1)

        # 控制台清除按钮
        ttk.Button(
            console_frame, text="清除控制台", command=self.clear_console, width=12
        ).grid(row=1, column=0, pady=5)

        # 添加标签页
        self.log_notebook.add(console_frame, text="控制台输出")
        self.log_notebook.add(packet_frame, text="数据包监控")

        # 上半部分 - 控制面板
        control_frame = ttk.LabelFrame(self.main_frame, text="控制面板", padding="5")
        control_frame.grid(
            row=0, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5
        )
        control_frame.columnconfigure(1, weight=1)

        # 网络接口选择（第一行）
        ttk.Label(control_frame, text="网络接口:").grid(
            row=0, column=0, sticky=tk.W, pady=5, padx=5
        )
        self.interface_combo = ttk.Combobox(
            control_frame, textvariable=self.selected_interface, state="readonly"
        )
        self.interface_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(
            control_frame, text="刷新", command=self.refresh_interfaces, width=8
        ).grid(row=0, column=2, padx=5)

        # 状态和控制按钮（第二行）
        self.capture_btn = ttk.Button(
            control_frame, text="开始捕获", command=self.toggle_capture, width=10
        )
        self.capture_btn.grid(row=1, column=0, pady=5, padx=5)
        ttk.Label(control_frame, text="状态:").grid(
            row=1, column=1, sticky=tk.W, padx=5
        )
        ttk.Label(control_frame, textvariable=self.status_text).grid(
            row=1, column=1, sticky=tk.W, padx=60
        )

        # 服务器地址显示
        ttk.Label(control_frame, text="推流服务器:").grid(
            row=2, column=0, sticky=tk.W, pady=5, padx=5
        )
        self.server_entry = ttk.Entry(control_frame, textvariable=self.server_address)
        self.server_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5)

        # 服务器地址操作按钮框
        server_btn_frame = ttk.Frame(control_frame)
        server_btn_frame.grid(row=2, column=2, padx=5)

        ttk.Button(
            server_btn_frame,
            text="复制",
            command=lambda: self.copy_to_clipboard(self.server_address.get()),
            width=8,
        ).pack(side=tk.LEFT, padx=2)

        # 创建控制面板
        self.control_panel = create_control_panel(self)

        # 创建日志面板
        self.log_panel = create_log_panel(self)

        # 添加底栏
        self.create_status_bar()

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

        # OBS按钮组
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

        # OBS按钮组
        obs_btn_frame2 = ttk.Frame(obs_frame)
        obs_btn_frame2.grid(row=2, column=0, columnspan=2, pady=(5, 2))

        ttk.Button(
            obs_btn_frame2,
            text="同步推流码",
            command=self.sync_stream_config,
            width=12,
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            obs_btn_frame2, text="启动OBS", command=self.launch_obs, width=12
        ).pack(side=tk.LEFT, padx=5)

        # OBS按钮组
        obs_btn_frame3 = ttk.Frame(obs_frame)
        obs_btn_frame3.grid(row=3, column=0, columnspan=2, pady=(5, 2))

        ttk.Button(
            obs_btn_frame3, text="插件管理", command=self.open_plugin_manager, width=12
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            obs_btn_frame3, text="使用说明", command=self.show_obs_help, width=12
        ).pack(side=tk.LEFT, padx=5)

        # 添加广告位面板
        ad_frame = ttk.LabelFrame(self.main_frame, text="联系我", padding="5")
        ad_frame.grid(row=1, column=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5, padx=5)
        ad_frame.columnconfigure(0, weight=1)

        try:
            github_icon = tk.PhotoImage(file=resource_path("assets/github.png"))
            # 创建一个无边框的Label来显示图标
            logo_label = ttk.Label(ad_frame, image=github_icon, cursor="hand2")
            logo_label.image = github_icon
            logo_label.grid(row=0, column=0, pady=(5, 2), padx=5)
            logo_label.bind("<Button-1>", lambda e: self.open_github())

            # 调整图片大小为原来的1/4
            github_icon = github_icon.subsample(4, 4)
            logo_label.configure(image=github_icon)
            logo_label.image = github_icon

            # 添加仓库地址链接
            repo_label = ttk.Label(
                ad_frame,
                text=GITHUB_CONFIG["REPO_URL"],
                cursor="hand2",
                foreground="blue",
                font=("", 9, "underline"),
            )
            repo_label.grid(row=1, column=0, pady=(0, 5), padx=5)
            repo_label.bind("<Button-1>", lambda e: self.open_github())

            # 添加广告文本区域
            self.ad_text = scrolledtext.ScrolledText(
                ad_frame, wrap=tk.WORD, width=20, height=15
            )
            self.ad_text.grid(
                row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5, padx=5
            )
            
            # 先显示默认广告内容
            self.ad_text.insert(tk.END, ADVERTISEMENT_TEXT)
            self.ad_text.configure(state="disabled")

            # 在窗口加载完成后异步获取广告内容
            self.root.after(1000, self.async_fetch_ad_content)

        except Exception:
            # 如果图标加载失败，使用文本链接样式的Label
            link_label = ttk.Label(
                ad_frame,
                text=GITHUB_CONFIG["REPO_URL"],
                cursor="hand2",
                foreground="blue",
            )
            link_label.grid(row=0, column=0, pady=5, padx=5)
            link_label.bind("<Button-1>", lambda e: self.open_github())

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

    def show_help(self):
        """显示使用说明弹窗"""
        # 创建对话框
        dialog = tk.Toplevel(self.root)
        dialog.title("使用说明")
        dialog.geometry("500x400")
        dialog.transient(self.root)  # 设置为主窗口的子窗口
        dialog.grab_set()  # 模态对话框

        # 添加文本区域
        text_area = scrolledtext.ScrolledText(
            dialog, wrap=tk.WORD, width=50, height=20, padx=10, pady=10
        )
        text_area.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        text_area.insert(tk.END, HELP_TEXT)
        text_area.configure(state="disabled")  # 设置为只读

        # 添加确定按钮
        ttk.Button(dialog, text="确定", command=dialog.destroy, width=10).pack(pady=10)

        # 居中显示
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")

    def show_disclaimer(self):
        """显示免责声明弹窗"""
        disclaimer_text = (
            "免责声明：\n\n"
            "1. 本软件仅供学习和研究使用，请勿用于任何商业用途。\n\n"
            "2. 使用本软件时请遵守相关法律法规，不得用于任何违法用途。\n\n"
            "3. 本软件开源免费，作者不对使用本软件造成的任何直接或间\n接损失负责。\n\n"
            "4. 使用本软件即表示您同意本免责声明的所有条款。\n\n"
            "5. 作者保留对本软件和免责声明的最终解释权。\n\n"
        )

        # 创建对话框
        dialog = tk.Toplevel(self.root)
        dialog.title("免责声明")
        dialog.geometry("500x400")
        dialog.transient(self.root)  # 设置为主窗口的子窗口
        dialog.grab_set()  # 模态对话框

        # 添加文本区域
        text_area = scrolledtext.ScrolledText(
            dialog, wrap=tk.WORD, width=50, height=20, padx=10, pady=10
        )
        text_area.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        text_area.insert(tk.END, disclaimer_text)
        text_area.configure(state="disabled")  # 设置为只读

        # 添加确定按钮
        ttk.Button(dialog, text="确定", command=dialog.destroy, width=10).pack(pady=10)

        # 居中显示
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")

    def show_about(self):
        """显示关于对话框"""
        about_text = (
            f"抖音直播推流地址获取工具\n"
            f"版本：{VERSION}\n"
            f"作者：关水来了\n\n"
            f"GitHub：{GITHUB_CONFIG['REPO_URL']}\n\n"
            f"本工具仅供学习交流使用"
        )
        messagebox.showinfo("关于", about_text)

    def open_github(self):
        """打开GitHub页面"""
        webbrowser.open(GITHUB_CONFIG["REPO_URL"])

    def clear_logs(self):
        """清除所有日志"""
        self.logger.clear_console()
        self.logger.clear_packet_console()

    def load_interfaces(self):
        """加载网络接口列表"""
        self.log_to_console("\n正在加载网络接口列表...")

        try:
            self.interfaces = get_windows_if_list()

            if self.interfaces:
                # 获取接口状态
                netsh_output = subprocess.check_output(
                    "netsh interface show interface", shell=True
                ).decode("gbk", errors="ignore")

                active_interfaces = []
                inactive_interfaces = []
                default_interface = None

                # 解析 netsh 输出获取接口状态
                interface_status = {}
                for line in netsh_output.split("\n")[3:]:
                    if line.strip():
                        parts = line.strip().split()
                        if len(parts) >= 4:
                            status = parts[0]
                            name = " ".join(parts[3:])
                            interface_status[name] = status == "已启用"

                for iface in self.interfaces:
                    name = iface["name"]
                    desc = iface["description"]
                    ip_addresses = iface.get("ips", [])

                    # 从 netsh 结果获取状态
                    is_active = interface_status.get(name, False)
                    status = "已连接" if is_active else "未连接"

                    # 格式化显示名称
                    display_name = f"[{status}] {name} - {desc[:47] + '...' if len(desc) > 50 else desc}"

                    # 分类接口
                    if is_active and ip_addresses:
                        active_interfaces.append((display_name, name, desc))
                        # 检查是否为以太网
                        if "ethernet" in desc.lower() or "以太网" in desc:
                            default_interface = display_name
                    else:
                        inactive_interfaces.append((display_name, name, desc))

                    # 打印详细信息到控制台
                    self.log_to_console(
                        f"接口: {name}\n"
                        f"   描述: {desc}\n"
                        f"   状态: {status}\n"
                        f"   IP地址: {', '.join(ip_addresses) if ip_addresses else '无'}\n"
                    )

                # 合并列表，活动接口在前
                interface_list = [x[0] for x in active_interfaces] + [
                    x[0] for x in inactive_interfaces
                ]

                # 更新下拉列表
                self.interface_combo["values"] = interface_list

                # 设置默认选择
                if default_interface:
                    # 如果有活动的以太网接口，选择它
                    self.selected_interface.set(default_interface)
                    self.log_to_console(f"自动选择以太网接口: {default_interface}")
                elif active_interfaces:
                    # 否则选择第一个活动接口
                    self.selected_interface.set(active_interfaces[0][0])
                    self.log_to_console(f"自动选择活动接口: {active_interfaces[0][0]}")
                elif interface_list:
                    # 如果没有活动接口，选择第一个可用接口
                    self.selected_interface.set(interface_list[0])
                    self.log_to_console("未找到活动接口，选择第一个可用接口")

                self.log_to_console(f"\n共找到 {len(self.interfaces)} 个网络接口")
                self.log_to_console(f"其中活动接口 {len(active_interfaces)} 个")

            else:
                self.log_to_console("未找到可用的网络接口")

        except Exception as e:
            self.log_to_console(f"加载网络接口失败: {str(e)}")
            import traceback

            self.log_to_console(traceback.format_exc())

    def refresh_interfaces(self):
        """刷新网络接口列表"""
        self.log_to_console("\n正在刷新网络接口列表...")
        self.load_interfaces()
        self.log_to_console("网络接口列表刷新完成")

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
            self.log_notebook.select(1)  # 切换到控制台输出标签

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

    def toggle_capture(self):
        """切换捕获状态"""
        if not self.is_capturing:
            # 获取选中的接口名称
            interface = (
                self.selected_interface.get().split(" - ")[0].split("]")[1].strip()
            )

            # 开始捕获
            self.is_capturing = True
            self.capture_btn.configure(text="停止捕获")
            self.interface_combo.configure(state=tk.DISABLED)
            self.status_text.set("正在捕获")

            # 清空原有推流地址和推流码
            self.update_stream_url("", "")

            # 启动捕获线程
            self.capture.start(interface)

        else:
            # 停止捕获
            self.is_capturing = False
            self.capture_btn.configure(text="开始捕获")
            self.interface_combo.configure(state="readonly")
            self.status_text.set("已停止")

            # 停止捕获线程
            self.capture.stop()

    def copy_to_clipboard(self, text):
        if not text.strip():
            messagebox.showinfo("提示", "没有内容可复制，请先按说明进行地址捕获")
            return

        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        messagebox.showinfo("成功", "已复制到剪贴板")

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

    def handle_rtmp_url(self, url):
        """处理捕获到的RTMP URL"""
        try:
            # 分离服务器地址和推流码
            if "?" in url:
                server = url.split("?")[0]
                code = url.split("?")[1]
            else:
                server = url
                code = ""

            # 更新界面
            self.server_address.set(server)
            self.stream_code.set(code)

        except Exception as e:
            self.logger.error(f"处理RTMP URL时出错: {str(e)}")

    def update_stream_url(self, server_address, stream_code):
        """更新推流地址和推流码"""
        self.server_address.set(server_address)
        self.stream_code.set(stream_code)

    def async_check_updates(self):
        """异步检查更新"""
        thread = threading.Thread(target=check_for_updates)
        thread.daemon = True  # 设置为守护线程，这样主程序退出时线程会自动结束
        thread.start()

    def on_capture_click(self):
        """处理捕获按钮点击事件"""
        if not self.is_capturing:
            # 开始捕获
            selected_interface = self.interface_combo.get()
            if not selected_interface:
                messagebox.showerror("错误", "请选择网络接口！")
                return

            self.capture.start(selected_interface)
            self.update_capture_status(True)
        else:
            # 停止捕获
            self.capture.stop()
            self.update_capture_status(False)

    def update_capture_status(self, is_capturing):
        """更新捕获状态和按钮显示"""
        self.is_capturing = is_capturing
        if is_capturing:
            self.capture_btn.config(text="停止捕获")
            self.status_text.set("状态：正在捕获...")
            self.interface_combo.config(state="disabled")
        else:
            self.capture_btn.config(text="开始捕获")
            self.status_text.set("状态：已停止")
            self.interface_combo.config(state="readonly")

    def on_capture_complete(self, server_address, stream_code):
        """捕获完成的回调函数"""
        # 更新界面显示
        self.update_stream_url(server_address, stream_code)
        # 停止捕获并更新状态
        self.capture.stop()
        self.update_capture_status(False)

    def configure_obs_path(self):
        """配置OBS路径"""
        from tkinter import filedialog
        import json
        import os

        file_path = filedialog.askopenfilename(
            title="选择obs64.exe",
            filetypes=[("EXE files", "*.exe")],
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
            self.log_to_console("OBS启动成功")

    def configure_stream(self):
        """配置推流设置"""
        import os
        from tkinter import filedialog

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

            # 可以在这里添加保存配置文件路径到config.json的逻辑
            self.save_stream_config_path(file_path)

    def save_stream_config_path(self, file_path):
        """保存推流配置路径到配置文件"""
        import json
        import os

        config_dir = os.path.expanduser("~/.douyin-rtmp")
        config_file = os.path.join(config_dir, "config.json")

        config = {}
        if os.path.exists(config_file):
            with open(config_file, "r", encoding="utf-8") as f:
                config = json.load(f)

        config["stream_config_path"] = file_path

        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

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

    def show_donation(self):
        """显示打赏对话框"""
        donation_window = tk.Toplevel()
        donation_window.title("感谢支持")
        donation_window.geometry("500x400")
        donation_window.resizable(False, False)
        try:
            # 使用 resource_path 加载图片
            coffee_icon = tk.PhotoImage(file=resource_path("assets/donate.png"))
            img_label = ttk.Label(donation_window, image=coffee_icon)
            img_label.image = coffee_icon  # 保持引用防止被垃圾回收
            img_label.pack(pady=10)
        except Exception as e:
            self.logger.error(f"加载打赏二维码失败: {str(e)}")
            error_label = ttk.Label(donation_window, text="二维码加载失败")
            error_label.pack(pady=10)

        thank_text = "无论多少都是心意，一分也是对我莫大的鼓励！谢谢您的支持！\n ps:直播有收入了随便来一点喜庆一下就好啦，学生党或者直播没收益就不用啦！当然，大佬请随意~ 预祝各位老师们大红大紫！"
        text_label = ttk.Label(donation_window, text=thank_text, wraplength=450)
        text_label.pack(pady=10)

    def sync_stream_config(self, from_launch_button=False):
        """同步推流配置到OBS"""
        server_url = self.server_address.get()
        stream_key = self.stream_code.get()
        server_url = '123123123aaa'
        stream_key = '124124124aaa'
        return self.obs_utils.sync_stream_config(server_url, stream_key, from_launch_button)

    def open_plugin_manager(self):
        """打开插件管理窗口"""
        from gui.plugin_manager import PluginManagerFrame
        
        # 创建新窗口
        plugin_window = tk.Toplevel(self.root)
        plugin_window.title("插件管理")
        plugin_window.geometry("400x300")
        
        # 使窗口模态
        plugin_window.transient(self.root)
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
        plugin_window.geometry('{}x{}+{}+{}'.format(width, height, x, y))

    def async_fetch_ad_content(self):
        """异步获取广告内容"""
        def fetch_content():
            try:
                import requests
                response = requests.get(
                    'https://gh-proxy.protoniot.com/heplex/douyin-rtmp/raw/config/ads', 
                    timeout=5
                )
                if response.status_code == 200:
                    self.root.after(0, self.update_ad_content, response.text)
            except Exception:
                pass

        thread = threading.Thread(target=fetch_content)
        thread.daemon = True
        thread.start()

    def update_ad_content(self, content):
        """更新广告内容"""
        try:
            self.ad_text.configure(state="normal")
            self.ad_text.delete(1.0, tk.END)
            self.ad_text.insert(tk.END, content)
            self.ad_text.configure(state="disabled")
        except Exception:
            pass
