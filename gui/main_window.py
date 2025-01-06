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
from utils.config import VERSION, GITHUB_CONFIG
import threading
from utils.version import check_for_updates

def resource_path(relative_path):
    """获取资源的绝对路径"""
    try:
        # PyInstaller创建临时文件夹，将路径存储在_MEIPASS中
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
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
        self.show_disclaimer()
        
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
        
        # 初始化组件
        self.logger = Logger()
        self.network = NetworkInterface(self.logger)
        self.npcap = NpcapManager(self.logger)
        self.capture = PacketCapture(self.logger)
        
        # 设置回调函数
        self.capture.add_callback(self.update_stream_url)
        
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
        help_menu.add_command(label="GitHub 仓库", 
                            command=lambda: webbrowser.open(GITHUB_CONFIG['RELEASE_URL']))
        help_menu.add_separator()
        help_menu.add_command(label=f"关于 (v{VERSION})", 
                            command=self.show_about)
        
        # 主布局使用网格
        self.main_frame.columnconfigure(1, weight=1)
        
        # 创建标签页控件
        self.log_notebook = ttk.Notebook(self.main_frame)
        self.log_notebook.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.main_frame.grid_rowconfigure(1, weight=1)
        
        # 创建数据包日志标签页
        packet_frame = ttk.Frame(self.log_notebook, padding="5")
        self.packet_console = scrolledtext.ScrolledText(packet_frame, wrap=tk.WORD, height=8)
        self.packet_console.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        packet_frame.grid_columnconfigure(0, weight=1)
        packet_frame.grid_rowconfigure(0, weight=1)
        
        # 数据包日志清除按钮
        ttk.Button(
            packet_frame,
            text="清除数据包日志",
            command=self.clear_packet_console,
            width=15
        ).grid(row=1, column=0, pady=5)
        
        # 创建主控制台标签页
        console_frame = ttk.Frame(self.log_notebook, padding="5")
        self.console = scrolledtext.ScrolledText(console_frame, wrap=tk.WORD, height=8)
        self.console.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        console_frame.grid_columnconfigure(0, weight=1)
        console_frame.grid_rowconfigure(0, weight=1)
        
        # 控制台清除按钮
        ttk.Button(
            console_frame,
            text="清除控制台",
            command=self.clear_console,
            width=12
        ).grid(row=1, column=0, pady=5)
        
        # 添加标签页
        self.log_notebook.add(console_frame, text="控制台输出")
        self.log_notebook.add(packet_frame, text="数据包监控")
        
        # 上半部分 - 控制面板
        control_frame = ttk.LabelFrame(self.main_frame, text="控制面板", padding="5")
        control_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        control_frame.columnconfigure(1, weight=1)
        
        # 网络接口选择（第一行）
        ttk.Label(control_frame, text="网络接口:").grid(row=0, column=0, sticky=tk.W, pady=5, padx=5)
        self.interface_combo = ttk.Combobox(
            control_frame, 
            textvariable=self.selected_interface,
            state="readonly"
        )
        self.interface_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(
            control_frame,
            text="刷新",
            command=self.refresh_interfaces,
            width=8
        ).grid(row=0, column=2, padx=5)
        
        # 状态和控制按钮（第二行）
        self.capture_btn = ttk.Button(
            control_frame, 
            text="开始捕获",
            command=self.toggle_capture,
            width=10
        )
        self.capture_btn.grid(row=1, column=0, pady=5, padx=5)
        ttk.Label(control_frame, text="状态:").grid(row=1, column=1, sticky=tk.W, padx=5)
        ttk.Label(control_frame, textvariable=self.status_text).grid(row=1, column=1, sticky=tk.W, padx=60)
        
        # 服务器地址显示
        ttk.Label(control_frame, text="推流服务器:").grid(row=2, column=0, sticky=tk.W, pady=5, padx=5)
        self.server_entry = ttk.Entry(control_frame, textvariable=self.server_address)
        self.server_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5)
        
        # 服务器地址操作按钮框
        server_btn_frame = ttk.Frame(control_frame)
        server_btn_frame.grid(row=2, column=2, padx=5)
        
        ttk.Button(
            server_btn_frame,
            text="复制",
            command=lambda: self.copy_to_clipboard(self.server_address.get()),
            width=8
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            server_btn_frame,
            text="清除",
            command=lambda: self.server_address.set(""),
            width=8
        ).pack(side=tk.LEFT, padx=2)
        
        # 创建控制面板
        self.control_panel = create_control_panel(self)
        
        # 创建日志面板
        self.log_panel = create_log_panel(self)
        
        # 创建使用说明面板
        self.help_panel = create_help_panel(self)
        
    def show_disclaimer(self):
        """显示免责声明"""
        disclaimer_text = (
            "免责声明\n\n"
            "1. 本工具仅供学习和研究使用，完全免费\n"
            "2. 请勿用于任何商业用途\n"
            "3. 使用本工具产生的一切后果由使用者自行承担\n"
            "4. 本工具使用了网络抓包技术，可能会被杀毒软件误报\n"
            "   这是因为抓包功能与某些恶意软件行为类似\n"
            "   本工具完全开源，源代码可在 GitHub 查看，请放心使用\n"
            "5. 继续使用则表示您同意以上条款"
        )
        response = messagebox.askokcancel("免责声明", disclaimer_text)
        if not response:
            self.root.quit()
        
    def show_about(self):
        """显示关于对话框"""
        about_text = (
            f"抖音直播推流地址获取工具\n"
            f"版本：{VERSION}\n"
            f"作者：kumquat\n\n"
            f"GitHub：{GITHUB_CONFIG['RELEASE_URL']}\n\n"
            f"本工具仅供学习交流使用"
        )
        messagebox.showinfo("关于", about_text)
        
    def open_github(self):
        """打开GitHub页面"""
        webbrowser.open(GITHUB_CONFIG['RELEASE_URL'])
        
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
                    "netsh interface show interface",
                    shell=True
                ).decode('gbk', errors='ignore')
                
                active_interfaces = []
                inactive_interfaces = []
                default_interface = None
                
                # 解析 netsh 输出获取接口状态
                interface_status = {}
                for line in netsh_output.split('\n')[3:]:
                    if line.strip():
                        parts = line.strip().split()
                        if len(parts) >= 4:
                            status = parts[0]
                            name = ' '.join(parts[3:])
                            interface_status[name] = status == "已启用"
                
                for iface in self.interfaces:
                    name = iface['name']
                    desc = iface['description']
                    ip_addresses = iface.get('ips', [])
                    
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
                interface_list = [x[0] for x in active_interfaces] + [x[0] for x in inactive_interfaces]
                
                # 更新下拉列表
                self.interface_combo['values'] = interface_list
                
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
            
    def show_about(self):
        """显示关于对话框"""
        about_text = (
            f"抖音直播推流地址获取工具\n"
            f"版本：{VERSION}\n"
            f"作者：kumquat\n\n"
            f"GitHub：{GITHUB_CONFIG['RELEASE_URL']}\n\n"
            f"本工具仅供学习交流使用"
        )
        messagebox.showinfo("关于", about_text)
        
    def show_disclaimer(self):
        """显示免责声明"""
        disclaimer_text = (
            "免责声明\n\n"
            "1. 本工具仅供学习和研究使用，完全免费\n"
            "2. 请勿用于任何商业用途\n"
            "3. 使用本工具产生的一切后果由使用者自行承担\n"
            "4. 本工具使用了网络抓包技术，可能会被杀毒软件误报\n"
            "   这是因为抓包功能与某些恶意软件行为类似\n"
            "   本工具完全开源，源代码可在 GitHub 查看，请放心使用\n"
            "5. 继续使用则表示您同意以上条款"
        )
        response = messagebox.askokcancel("免责声明", disclaimer_text)
        if not response:
            self.root.quit() 

    def toggle_capture(self):
        """切换捕获状态"""
        if not self.is_capturing:
            # 获取选中的接口名称
            interface = self.selected_interface.get().split(" - ")[0].split("]")[1].strip()
            
            # 开始捕获
            self.is_capturing = True
            self.capture_btn.configure(text="停止捕获")
            self.interface_combo.configure(state=tk.DISABLED)
            self.status_text.set("正在捕获")
            
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