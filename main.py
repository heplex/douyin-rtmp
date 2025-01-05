import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import re
import os
import sys
import webbrowser
import winreg
from datetime import datetime
from scapy.all import sniff, IP, TCP, Raw
from scapy.arch.windows import get_windows_if_list

class StreamCaptureGUI:
    VERSION = "1.0.0"  # 添加版本号
    GITHUB_URL = "https://github.com/heplex/douyin-rtmp.git"
    
    def __init__(self, root):
        self.root = root
        self.root.title(f"抖音直播推流地址获取工具 v{self.VERSION}")
        self.root.geometry("800x600")
        
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
        
        # 添加网络接口变量
        self.interfaces = []
        self.selected_interface = tk.StringVar()
        
        # 先创建界面
        self.create_widgets()
        
        # 再加载网络接口
        self.load_interfaces()
        
        # 最后检查Npcap
        if not self.check_npcap():
            self.check_and_install_npcap()
            sys.exit(1)

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
        help_menu.add_command(label="GitHub 仓库", command=lambda: webbrowser.open(self.GITHUB_URL))
        help_menu.add_separator()
        help_menu.add_command(label=f"关于 (v{self.VERSION})", 
                            command=self.show_about)
        
        # 主布局使用网格
        self.main_frame.columnconfigure(1, weight=1)
        
        # 分割主界面为上下两部分
        main_paned = ttk.PanedWindow(self.main_frame, orient=tk.VERTICAL)
        main_paned.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.main_frame.grid_rowconfigure(1, weight=1)
        
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
        control_frame.columnconfigure(1, weight=1)  # 让第二列可以扩展
        
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
            width=6
        ).grid(row=0, column=0, padx=2)
        ttk.Button(
            server_btn_frame,
            text="清除",
            command=lambda: self.server_address.set(""),
            width=6
        ).grid(row=0, column=1, padx=2)
        
        # 推流码显示
        ttk.Label(control_frame, text="推流码:").grid(row=3, column=0, sticky=tk.W, pady=5, padx=5)
        self.code_entry = ttk.Entry(control_frame, textvariable=self.stream_code)
        self.code_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), padx=5)
        
        # 推流码操作按钮框
        code_btn_frame = ttk.Frame(control_frame)
        code_btn_frame.grid(row=3, column=2, padx=5)
        ttk.Button(
            code_btn_frame,
            text="复制",
            command=lambda: self.copy_to_clipboard(self.stream_code.get()),
            width=6
        ).grid(row=0, column=0, padx=2)
        ttk.Button(
            code_btn_frame,
            text="清除",
            command=lambda: self.stream_code.set(""),
            width=6
        ).grid(row=0, column=1, padx=2)
        
        # 使用说明
        help_frame = ttk.LabelFrame(self.main_frame, text="使用说明", padding="5")
        help_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        help_text = """
1. 请以管理员权限运行本程序
2. 选择正确的网络接口
3. 打开抖音直播伴侣
4. 点击"开始捕获"按钮
5. 在抖音直播伴侣中点击"开始直播"
6. 等待推流地址自动获取
7. 如果不能正常获取，可以点击工具，尝试重新安装Npcap
8. 在工具也可以卸载Npcap
        """
        ttk.Label(help_frame, text=help_text, justify=tk.LEFT).grid(row=0, column=0, sticky=tk.W)

    def log_to_console(self, message):
        """向控制台输出日志"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.console.insert(tk.END, f"[{current_time}] {message}\n")
        self.console.see(tk.END)  # 自动滚动到最新内容

    def clear_console(self):
        """清除控制台内容"""
        self.console.delete(1.0, tk.END)
        self.log_to_console("控制台已清除")

    def copy_to_clipboard(self, text):
        if not text:
            messagebox.showwarning("警告", "没有内容可复制！")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        messagebox.showinfo("提示", "已复制到剪贴板！")
        self.log_to_console(f"已复制内容: {text}")

    def toggle_capture(self):
        if not self.is_capturing:
            self.start_capture()
        else:
            self.stop_capture()

    def start_capture(self):
        # 检查是否选择了网络接口
        if not self.selected_interface.get():
            messagebox.showerror("错误", "请先选择网络接口！")
            return
            
        self.is_capturing = True
        self.capture_btn.configure(text="停止捕获")
        self.status_text.set("正在捕获...")
        self.server_address.set("")
        self.stream_code.set("")
        self.log_to_console("开始捕获数据包...")
        
        # 在新线程中开始捕获
        self.capture_thread = threading.Thread(target=self.capture_packets)
        self.capture_thread.daemon = True
        self.capture_thread.start()

    def stop_capture(self):
        self.is_capturing = False
        self.capture_btn.configure(text="开始捕获")
        self.status_text.set("已停止")
        self.log_to_console("停止捕获数据包")

    def capture_packets(self):
        def packet_callback(packet):
            if not self.is_capturing:
                return True
            
            if IP in packet and TCP in packet and Raw in packet:
                try:
                    # 获取基本信息
                    src_ip = packet[IP].src
                    dst_ip = packet[IP].dst
                    src_port = packet[TCP].sport
                    dst_port = packet[TCP].dport
                    payload = packet[Raw].load.decode('utf-8', errors='ignore')
                    
                    # 输出基本连接信息到数据包日志
                    self.root.after(0, lambda: self.log_packet(
                        f"捕获数据包: {src_ip}:{src_port} -> {dst_ip}:{dst_port}"
                    ))
                    
                    # 查找推流服务器地址
                    if not self.server_address.get():
                        if 'connect' in payload and 'thirdgame' in payload:
                            self.log_to_console("\n>>> 发现RTMP连接数据包 <<<")
                            server_match = re.search(r'(rtmp://[^"\'\s]+/thirdgame)', payload)
                            if server_match:
                                server = server_match.group(1)
                                self.server_address.set(server)
                                self.log_to_console(f"找到推流服务器地址: {server}")
                    
                    # 查找推流码
                    if not self.stream_code.get():
                        if 'FCPublish' in payload:
                            self.log_to_console("\n>>> 发现FCPublish数据包 <<<")
                            # 先匹配基本模式
                            code_match = re.search(r'stream-\d+\?[^"\'\s]+', payload)
                            if code_match:
                                # 获取匹配的字符串
                                code = code_match.group(0)
                                # 只保留合法字符：小写字母、数字、连字符、问号、等号、&符号和大写S/T
                                code = re.sub(r'[^a-z0-9ST\-?=&]', '', code)
                                self.stream_code.set(code)
                                self.log_to_console(f"找到推流码: {code}")
                    
                    # 如果都找到了，停止捕获
                    if self.server_address.get() and self.stream_code.get():
                        self.root.after(0, self.stop_capture)
                        self.status_text.set("捕获完成")
                        self.log_to_console("\n已成功获取所有信息！")
                        return True
                        
                except Exception as e:
                    self.log_to_console(f"处理数据包时出错: {str(e)}")
            
            return None

        try:
            # 检查是否选择了接口
            if not self.selected_interface.get():
                raise Exception("请先选择网络接口")
            
            self.log_to_console("\n开始监听网络数据包...")
            
            # 从显示名称中提取原始接口名称
            selected_display = self.selected_interface.get()
            selected = selected_display.split('] ')[1].split(' - ')[0]
            
            self.log_to_console(f"使用网络接口: {selected}，点击数据包监控查看详细数据包。")
            
            # 验证接口是否存在
            valid_interface = False
            for iface in self.interfaces:
                if iface['name'] == selected:
                    valid_interface = True
                    break
                
            if not valid_interface:
                raise Exception(f"无效的网络接口: {selected}")
            
            # 捕获所有TCP流量
            sniff(
                iface=selected,
                filter="tcp",
                prn=packet_callback,
                store=0,
                stop_filter=lambda p: not self.is_capturing
            )
        except Exception as e:
            error_msg = f"捕获出错: {str(e)}"
            self.log_to_console(error_msg)
            self.root.after(0, lambda: messagebox.showerror("错误", error_msg))
            self.root.after(0, self.stop_capture)

    def check_npcap(self):
        """检查Npcap是否已安装"""
        try:
            # 添加调试信息
            self.log_to_console("开始检查Npcap安装状态...")
            
            reg_paths = [
                r"SOFTWARE\Npcap",
                r"SOFTWARE\WOW6432Node\Npcap",
                r"SYSTEM\CurrentControlSet\Services\Npcap"
            ]
            
            for path in reg_paths:
                try:
                    self.log_to_console(f"检查注册表路径: {path}")
                    winreg.OpenKey(
                        winreg.HKEY_LOCAL_MACHINE,
                        path,
                        0,
                        winreg.KEY_READ | winreg.KEY_WOW64_64KEY
                    )
                    self.log_to_console("在注册表中找到Npcap")
                    return True
                except WindowsError as we:
                    self.log_to_console(f"路径 {path} 检查失败: {we}")
                    continue
            
            npcap_dir = r"C:\Windows\System32\Npcap"
            self.log_to_console(f"检查Npcap文件夹: {npcap_dir}")
            if os.path.exists(npcap_dir):
                self.log_to_console("找到Npcap文件夹")
                return True
            
            self.log_to_console("未找到Npcap安装")
            return False
            
        except Exception as e:
            self.log_to_console(f"检查Npcap时出错: {e}")
            return False

    def show_npcap_warning(self):
        """显示Npcap未安装警告"""
        response = messagebox.askquestion(
            "缺少必要组件",
            "检测到未安装Npcap，该组件是程序运行必需的。\n是否立即前往下载？",
            icon='warning'
        )
        if response == 'yes':
            webbrowser.open('https://npcap.com/#download')

    def check_and_install_npcap(self):
        """检查并安装Npcap"""
        if self.check_npcap():
            return True
        
        response = messagebox.askquestion(
            "缺少必要组件",
            "检测到未安装Npcap，是否立即安装？\n(需要管理员权限)",
            icon='warning'
        )
        
        if response == 'yes':
            try:
                # 修改这部分代码来处理打包后的资源路径
                if getattr(sys, 'frozen', False):
                    # 如果是打包后的程序
                    application_path = sys._MEIPASS
                else:
                    # 如果是开发环境
                    application_path = os.path.dirname(__file__)
                
                npcap_installer = os.path.join(application_path, "resources", "npcap-1.80.exe")
                
                if os.path.exists(npcap_installer):
                    self.log_to_console(f"正在启动Npcap安装程序: {npcap_installer}")
                    os.startfile(npcap_installer)
                    messagebox.showinfo("提示", "请完成Npcap安装后重启程序")
                else:
                    self.log_to_console(f"未找到Npcap安装程序: {npcap_installer}")
                    # 如果本地没有安装包，跳转到下载页面
                    webbrowser.open('https://npcap.com/#download')
                sys.exit(0)
            except Exception as e:
                error_msg = f"安装Npcap失败: {str(e)}"
                self.log_to_console(error_msg)
                messagebox.showerror("错误", error_msg)
                sys.exit(1)
        return False

    def uninstall_npcap(self):
        """卸载Npcap"""
        try:
            # 确认是否卸载
            if not messagebox.askyesno("确认", 
                "确定要卸载Npcap吗？\n卸载后需要重新安装才能使用本程序。"):
                return
                
            # 查找Npcap卸载程序
            uninstall_paths = [
                r"C:\Program Files\Npcap\unins000.exe",
                r"C:\Program Files (x86)\Npcap\unins000.exe"
            ]
            
            uninstaller = None
            for path in uninstall_paths:
                if os.path.exists(path):
                    uninstaller = path
                    break
            
            if uninstaller:
                self.log_to_console("正在启动Npcap卸载程序...")
                os.startfile(uninstaller)
                messagebox.showinfo("提示", "请完成Npcap卸载后重启程序")
                sys.exit(0)
            else:
                # 如果找不到卸载程序，打开控制面板
                self.log_to_console("未找到Npcap卸载程序，正在打开控制面板...")
                os.system('control appwiz.cpl')
                messagebox.showinfo("提示", 
                    "请在控制面板中找到并卸载Npcap，\n完成后重启程序。")
                
        except Exception as e:
            error_msg = f"卸载Npcap时出错: {str(e)}"
            self.log_to_console(error_msg)
            messagebox.showerror("错误", error_msg)

    def load_interfaces(self):
        """加载网络接口列表"""
        try:
            self.interfaces = get_windows_if_list()
            if self.interfaces:
                interface_list = []
                active_interfaces = []
                inactive_interfaces = []
                default_interface = None
                
                # 使用 Windows 命令获取网络接口状态
                import subprocess
                netsh_output = subprocess.check_output(
                    "netsh interface show interface",
                    shell=True
                ).decode('gbk', errors='ignore')
                
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
        """清除数据包日志"""
        self.packet_console.delete(1.0, tk.END)

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
            if getattr(sys, 'frozen', False):
                application_path = sys._MEIPASS
            else:
                application_path = os.path.dirname(__file__)
            
            npcap_installer = os.path.join(application_path, "resources", "npcap-1.80.exe")
            
            if os.path.exists(npcap_installer):
                self.log_to_console("正在启动 Npcap 安装程序...")
                os.startfile(npcap_installer)
                messagebox.showinfo("提示", "请按照向导完成 Npcap 安装")
            else:
                self.log_to_console("未找到本地 Npcap 安装程序，正在跳转到下载页面...")
                webbrowser.open('https://npcap.com/#download')
                messagebox.showinfo("提示", "请从官网下载并安装 Npcap")
        except Exception as e:
            error_msg = f"启动 Npcap 安装程序失败: {str(e)}"
            self.log_to_console(error_msg)
            messagebox.showerror("错误", error_msg)

    def show_about(self):
        """显示关于对话框"""
        about_text = (
            f"抖音直播推流地址获取工具\n"
            f"版本：{self.VERSION}\n"
            f"作者：kumquat\n\n"
            f"GitHub：{self.GITHUB_URL}\n\n"
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

def main():
    # 检查是否以管理员权限运行
    if not is_admin():
        messagebox.showerror("错误", "请以管理员权限运行此程序！")
        return

    root = tk.Tk()
    app = StreamCaptureGUI(root)
    root.mainloop()

def is_admin():
    """检查是否以管理员权限运行"""
    try:
        return os.getuid() == 0
    except AttributeError:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0

if __name__ == "__main__":
    main()
