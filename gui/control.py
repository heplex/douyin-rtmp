import tkinter as tk
from tkinter import ttk, messagebox
from utils.network import NetworkInterface
from core.capture import PacketCapture

class ControlPanel:
    def __init__(self, gui):
        self.gui = gui
        self.network_interface = NetworkInterface(self.gui.logger)
        self.capture = PacketCapture(self.gui.logger)
        self.capture.add_callback(self.handle_rtmp_url)
        
        # 状态变量 - 移到frame创建之前
        self.is_capturing = False
        self.status_text = tk.StringVar(value="待开始")
        self.selected_interface = tk.StringVar()  # 确保在使用前初始化
        
        self.frame = self.create_control_panel()
        self.load_interfaces()
        
    def create_control_panel(self):
        """创建控制面板"""
        frame = ttk.LabelFrame(self.gui.main_frame, text="控制面板", padding="5")
        frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        frame.columnconfigure(1, weight=1)

        # 网络接口选择（第一行）
        ttk.Label(frame, text="网络接口:").grid(
            row=0, column=0, sticky=tk.W, pady=5, padx=5
        )
        self.interface_combo = ttk.Combobox(
            frame, textvariable=self.selected_interface, state="readonly", width=50
        )
        self.interface_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)

        # 刷新按钮
        ttk.Button(frame, text="刷新", command=self.refresh_interfaces, width=8).grid(
            row=0, column=2, padx=5
        )

        # 状态和控制按钮（第二行）
        self.capture_btn = ttk.Button(
            frame, text="开始捕获", command=self.toggle_capture, width=10
        )
        self.capture_btn.grid(row=1, column=0, pady=5, padx=5)
        ttk.Label(frame, text="状态:").grid(row=1, column=1, sticky=tk.W, padx=5)
        ttk.Label(frame, textvariable=self.status_text).grid(
            row=1, column=1, sticky=tk.W, padx=60
        )

        # 服务器地址显示（第三行）
        ttk.Label(frame, text="推流服务器:").grid(
            row=2, column=0, sticky=tk.W, pady=5, padx=5
        )
        self.server_entry = ttk.Entry(
            frame, textvariable=self.gui.server_address, state="readonly"
        )
        self.server_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5)

        # 服务器地址操作按钮框
        server_btn_frame = ttk.Frame(frame)
        server_btn_frame.grid(row=2, column=2, padx=5)

        ttk.Button(
            server_btn_frame,
            text="复制",
            command=lambda: self.copy_to_clipboard(self.gui.server_address.get()),
            width=8,
        ).pack(side=tk.LEFT, padx=2)

        # 推流码显示（第四行）
        ttk.Label(frame, text="推流码:").grid(row=3, column=0, sticky=tk.W, pady=5, padx=5)
        self.stream_entry = ttk.Entry(frame, textvariable=self.gui.stream_code, state="readonly")
        self.stream_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), padx=5)

        # 推流码操作按钮框
        stream_btn_frame = ttk.Frame(frame)
        stream_btn_frame.grid(row=3, column=2, padx=5)

        ttk.Button(
            stream_btn_frame,
            text="复制",
            command=lambda: self.copy_to_clipboard(self.gui.stream_code.get()),
            width=8,
        ).pack(side=tk.LEFT, padx=2)

        return frame

    def load_interfaces(self):
        """加载网络接口列表"""
        self.gui.log_to_console("\n正在加载网络接口列表...")
        
        result = self.network_interface.load_interfaces()
        interfaces = result['interfaces']
        
        if interfaces:
            # 更新下拉列表
            self.interface_combo["values"] = interfaces
            
            # 设置默认选择
            if result['default']:
                self.selected_interface.set(result['default'])
                self.gui.log_to_console(f"自动选择以太网接口: {result['default']}")
            else:
                self.selected_interface.set(interfaces[0])
                self.gui.log_to_console(f"自动选择第一个可用接口: {interfaces[0]}")
            
            self.gui.log_to_console(f"\n共找到 {len(interfaces)} 个网络接口")
            self.gui.log_to_console(f"其中活动接口 {result['active_count']} 个")
        else:
            self.gui.log_to_console("未找到可用的网络接口")

    def refresh_interfaces(self):
        """刷新网络接口列表"""
        self.gui.log_to_console("\n正在刷新网络接口列表...")
        self.load_interfaces()
        self.gui.log_to_console("网络接口列表刷新完成")

    def toggle_capture(self):
        """切换捕获状态"""
        if not self.is_capturing:
            # 获取选中的接口名称
            selected_interface = self.selected_interface.get()
            if not selected_interface:
                messagebox.showerror("错误", "请先选择网络接口")
                return
                
            # 从显示名称中提取实际的接口名称（第一个方括号之前的部分）
            interface = selected_interface.split(" [")[0].strip()

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
        """复制内容到剪贴板"""
        if not text.strip():
            messagebox.showinfo("提示", "没有内容可复制，请先按说明进行地址捕获")
            return

        self.gui.root.clipboard_clear()
        self.gui.root.clipboard_append(text)
        messagebox.showinfo("成功", "已复制到剪贴板")

    def update_capture_status(self, is_capturing):
        """更新捕获状态和按钮显示"""
        if is_capturing:
            self.capture_btn.config(text="停止捕获")
            self.status_text.set("正在捕获")
            self.interface_combo.config(state="disabled")
        else:
            self.capture_btn.config(text="开始捕获")
            self.status_text.set("已停止")
            self.interface_combo.config(state="readonly") 

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
            self.gui.server_address.set(server)
            self.gui.stream_code.set(code)

        except Exception as e:
            self.gui.logger.error(f"处理RTMP URL时出错: {str(e)}")

    def update_stream_url(self, server_address, stream_code):
        """更新推流地址和推流码"""
        self.gui.server_address.set(server_address)
        self.gui.stream_code.set(stream_code)

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

    def on_capture_complete(self, server_address, stream_code):
        """捕获完成的回调函数"""
        # 更新界面显示
        self.update_stream_url(server_address, stream_code)
        # 停止捕获并更新状态
        self.capture.stop()
        self.update_capture_status(False) 