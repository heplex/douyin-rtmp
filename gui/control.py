import tkinter as tk
from tkinter import ttk, messagebox
from utils.network import NetworkInterface
from core.capture import PacketCapture


class ControlPanel:
    def __init__(self, gui):
        self.gui = gui
        self.network_interface = NetworkInterface(self.gui.logger)
        self.capture = PacketCapture(self.gui.logger)
        self.capture.add_callback(self.update_stream_url)

        # 状态变量 - 移到frame创建之前
        self.is_capturing = False
        self.status_text = tk.StringVar(value="待开始")
        self.selected_interface = tk.StringVar()  # 确保在使用前初始化

        self.frame = self.create_control_panel()
        self.load_interfaces()

    def create_control_panel(self):
        """创建控制面板"""
        frame = ttk.LabelFrame(self.gui.main_frame, text="控制面板", padding="5")
        frame.grid(
            row=0, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5
        )
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
        self.refresh_btn = ttk.Button(frame, text="刷新", command=self.refresh_interfaces, width=8)
        self.refresh_btn.grid(row=0, column=2, padx=5)

        # 状态和控制按钮（第二行）
        self.capture_btn = ttk.Button(
            frame, text="开始捕获", command=self.toggle_capture, width=10
        )
        self.capture_btn.grid(row=1, column=0, pady=5, padx=5)
        ttk.Label(frame, text="状态:").grid(row=1, column=1, sticky=tk.W, padx=5)
        ttk.Label(frame, textvariable=self.status_text).grid(
            row=1, column=1, sticky=tk.W, padx=60
        )
        
        # 添加监听所有端口的复选框
        self.listening_all = tk.BooleanVar(value=True)  # 默认为True
        self.load_listening_config()  # 加载配置
        self.listen_all_check = ttk.Checkbutton(
            frame, 
            text="监听所有接口",
            variable=self.listening_all,
            command=self.on_listening_changed,
            width=15  # 增加宽度确保文字完全显示
        )
        self.listen_all_check.grid(row=1, column=1, sticky=tk.E, padx=(200, 5))

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
        ttk.Label(frame, text="推流码:").grid(
            row=3, column=0, sticky=tk.W, pady=5, padx=5
        )
        self.stream_entry = ttk.Entry(
            frame, textvariable=self.gui.stream_code, state="readonly"
        )
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
        interfaces = result["interfaces"]

        if interfaces:
            # 更新下拉列表
            self.interface_combo["values"] = interfaces

            # 设置默认选择
            if result["default"]:
                self.selected_interface.set(result["default"])
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

            # 开始捕获
            self.is_capturing = True
            self.capture_btn.configure(text="停止捕获")
            self.interface_combo.configure(state=tk.DISABLED)
            self.status_text.set("正在捕获")

            # 清空原有推流地址和推流码
            self.update_stream_url("", "")

            # 启动捕获线程，传递完整的接口显示名称
            self.capture.start(selected_interface)
        else:
            # 停止捕获
            self.is_capturing = False
            self.capture_btn.configure(text="开始捕获")
            self.on_listening_changed()
            self.status_text.set("已停止")
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

    def load_listening_config(self):
        """加载监听配置"""
        from utils.config import get_config

        listening_all = get_config("listening_all")
        if listening_all is not None:
            self.listening_all.set(listening_all)
        else:
            # 如果配置不存在，设置默认值为True并保存
            self.save_listening_config()
            
        # 初始化时设置接口选择的状态
        self.on_listening_changed()

    def save_listening_config(self):
        """保存监听配置"""
        from utils.config import set_config

        set_config("listening_all", self.listening_all.get())

    def on_listening_changed(self):
        """监听设置改变时的回调"""
        self.save_listening_config()
        
        # 根据监听所有接口的状态设置接口选择和刷新按钮的状态
        if self.listening_all.get():
            self.interface_combo.configure(state="disabled")
            self.refresh_btn.configure(state="disabled")
        else:
            self.interface_combo.configure(state="readonly")
            self.refresh_btn.configure(state="normal")

    def stop_capture(self):
        """停止捕获"""
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.stop()
            self.capture_thread.join()
            self.capture_thread = None
            
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        
        # 根据监听所有接口的状态重新设置接口选择框的状态
        self.on_listening_changed()
