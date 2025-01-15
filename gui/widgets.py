import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext


def create_control_panel(gui):
    """创建控制面板"""
    frame = ttk.LabelFrame(gui.main_frame, text="控制面板", padding="5")
    frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
    frame.columnconfigure(1, weight=1)

    # 网络接口选择（第一行）
    ttk.Label(frame, text="网络接口:").grid(
        row=0, column=0, sticky=tk.W, pady=5, padx=5
    )
    gui.interface_combo = ttk.Combobox(
        frame, textvariable=gui.selected_interface, state="readonly", width=50
    )
    gui.interface_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)

    # 刷新按钮
    ttk.Button(frame, text="刷新", command=gui.refresh_interfaces, width=8).grid(
        row=0, column=2, padx=5
    )

    # 状态和控制按钮（第二行）
    gui.capture_btn = ttk.Button(
        frame, text="开始捕获", command=gui.toggle_capture, width=10
    )
    gui.capture_btn.grid(row=1, column=0, pady=5, padx=5)
    ttk.Label(frame, text="状态:").grid(row=1, column=1, sticky=tk.W, padx=5)
    ttk.Label(frame, textvariable=gui.status_text).grid(
        row=1, column=1, sticky=tk.W, padx=60
    )

    # 服务器地址显示（第三行）
    ttk.Label(frame, text="推流服务器:").grid(
        row=2, column=0, sticky=tk.W, pady=5, padx=5
    )
    gui.server_entry = ttk.Entry(
        frame, textvariable=gui.server_address, state="readonly"
    )
    gui.server_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5)

    # 服务器地址操作按钮框
    server_btn_frame = ttk.Frame(frame)
    server_btn_frame.grid(row=2, column=2, padx=5)

    ttk.Button(
        server_btn_frame,
        text="复制",
        command=lambda: gui.copy_to_clipboard(gui.server_address.get()),
        width=8,
    ).pack(side=tk.LEFT, padx=2)

    # 推流码显示（第四行）
    ttk.Label(frame, text="推流码:").grid(row=3, column=0, sticky=tk.W, pady=5, padx=5)
    gui.stream_entry = ttk.Entry(frame, textvariable=gui.stream_code, state="readonly")
    gui.stream_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), padx=5)

    # 推流码操作按钮框
    stream_btn_frame = ttk.Frame(frame)
    stream_btn_frame.grid(row=3, column=2, padx=5)

    ttk.Button(
        stream_btn_frame,
        text="复制",
        command=lambda: gui.copy_to_clipboard(gui.stream_code.get()),
        width=8,
    ).pack(side=tk.LEFT, padx=2)

    return frame


def create_log_panel(gui):
    """创建日志面板"""
    # 创建标签页控件
    notebook = ttk.Notebook(gui.main_frame)
    notebook.grid(
        row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5
    )
    gui.main_frame.grid_rowconfigure(1, weight=1)

    # 创建系统日志标签页
    console_frame = ttk.Frame(notebook, padding="5")
    system_console = scrolledtext.ScrolledText(console_frame, wrap=tk.WORD, height=8)
    system_console.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    console_frame.grid_columnconfigure(0, weight=1)
    console_frame.grid_rowconfigure(0, weight=1)

    # 系统日志清除按钮
    ttk.Button(
        console_frame, text="清除控制台", command=gui.clear_console, width=12
    ).grid(row=1, column=0, pady=5)

    # 创建数据包日志标签页
    packet_frame = ttk.Frame(notebook, padding="5")
    packet_console = scrolledtext.ScrolledText(packet_frame, wrap=tk.WORD, height=8)
    packet_console.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    packet_frame.grid_columnconfigure(0, weight=1)
    packet_frame.grid_rowconfigure(0, weight=1)

    # 数据包日志清除按钮
    ttk.Button(
        packet_frame, text="清除数据包日志", command=gui.clear_packet_console, width=15
    ).grid(row=1, column=0, pady=5)

    # 添加标签页
    notebook.add(console_frame, text="控制台输出")
    notebook.add(packet_frame, text="数据包监控")

    # 设置日志控件
    gui.logger.set_consoles(system_console, packet_console)

    # 添加右键菜单
    def create_context_menu(widget, is_packet=False):
        menu = tk.Menu(widget, tearoff=0)
        menu.add_command(label="复制", command=lambda: copy_text(widget))
        menu.add_command(
            label="清除",
            command=gui.clear_packet_console if is_packet else gui.clear_console,
        )
        return menu

    def show_context_menu(event, menu):
        menu.post(event.x_root, event.y_root)

    def copy_text(widget):
        try:
            text = widget.get("sel.first", "sel.last")
            if text:
                widget.clipboard_clear()
                widget.clipboard_append(text)
                widget.update()
        except tk.TclError:
            pass

    system_menu = create_context_menu(system_console, False)
    packet_menu = create_context_menu(packet_console, True)

    system_console.bind("<Button-3>", lambda e: show_context_menu(e, system_menu))
    packet_console.bind("<Button-3>", lambda e: show_context_menu(e, packet_menu))

    return notebook


def create_help_panel(gui):
    """创建使用说明面板"""
    frame = ttk.LabelFrame(gui.main_frame, text="使用说明", padding="5")
    frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

    help_text = (
        "使用说明：\n"
        "1. 选择正确的网卡（一般是以太网或无线网卡）\n"
        "2. 点击[开始捕获]，查看数据包监控是否有流量，没有任何输出说明网卡选择错误\n"
        "3. 在抖音直播伴侣中点击[开始直播]\n"
        "4. 等待推流地址自动显示\n"
        "5. 点击复制即可\n\n"
        "注意：\n"
        "1. 如果不能正常获取，可以点击工具，尝试重新安装Npcap；\n"
        "2. 关闭电脑中有大量流量请求的应用，可能会干扰到推流地址的获取；\n"
    )

    help_label = ttk.Label(frame, text=help_text, justify=tk.LEFT)
    help_label.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)

    return frame
