import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from utils.content_config import HELP_TEXT


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
    
    # 保存packet_console的引用
    gui.packet_console = packet_console

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

def create_help_dialog(parent):
    """创建使用说明对话框"""
    dialog = tk.Toplevel(parent)
    dialog.title("使用说明")
    dialog.geometry("500x400")
    dialog.transient(parent)  # 设置为主窗口的子窗口
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

def create_disclaimer_dialog(parent):
    """创建免责声明对话框"""
    disclaimer_text = (
        "免责声明：\n\n"
        "1. 本软件仅供学习和研究使用，请勿用于任何商业用途。\n\n"
        "2. 使用本软件时请遵守相关法律法规，不得用于任何违法用途。\n\n"
        "3. 本软件开源免费，作者不对使用本软件造成的任何直接或间\n接损失负责。\n\n"
        "4. 使用本软件即表示您同意本免责声明的所有条款。\n\n"
        "5. 作者保留对本软件和免责声明的最终解释权。\n\n"
    )

    dialog = tk.Toplevel(parent)
    dialog.title("免责声明")
    dialog.geometry("500x400")
    dialog.transient(parent)  # 设置为主窗口的子窗口
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

def create_donation_dialog(parent, logger, resource_path):
    """创建打赏对话框"""
    donation_window = tk.Toplevel(parent)
    donation_window.title("感谢支持")
    donation_window.geometry("550x600")
    donation_window.resizable(False, False)
    donation_window.transient(parent)  # 设置为主窗口的子窗口
    
    # 创建主框架并添加内边距
    main_frame = ttk.Frame(donation_window, padding="20")
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # 添加标题
    title_label = ttk.Label(
        main_frame, 
        text="请作者喝杯咖啡", 
        font=("微软雅黑", 16, "bold")
    )
    title_label.pack(pady=(0, 20))

    try:
        # 使用 resource_path 加载图片
        coffee_icon = tk.PhotoImage(file=resource_path("assets/donate.png"))
        img_label = ttk.Label(main_frame, image=coffee_icon)
        img_label.image = coffee_icon  # 保持引用防止被垃圾回收
        img_label.pack(pady=(0, 20))
    except Exception as e:
        logger.error(f"加载打赏二维码失败: {str(e)}")
        error_label = ttk.Label(main_frame, text="二维码加载失败")
        error_label.pack(pady=(0, 20))

    # 添加感谢文本
    thank_text = (
        "感谢您的支持！\n\n"
        "无论多少都是心意，一分也是对我莫大的鼓励！\n"
        "学生党或者直播没收益就不用啦！当然，大佬请随意~\n"
        "预祝各位老师们大红大紫！"
    )
    text_label = ttk.Label(
        main_frame, 
        text=thank_text, 
        wraplength=400,
        justify="center",
        font=("微软雅黑", 10)
    )
    text_label.pack(pady=(0, 20))
    
    # 添加关闭按钮
    close_btn = ttk.Button(
        main_frame, 
        text="关闭", 
        command=donation_window.destroy,
        width=15
    )
    close_btn.pack(pady=(0, 10))
    
    # 居中显示窗口
    donation_window.update_idletasks()
    width = donation_window.winfo_width()
    height = donation_window.winfo_height()
    x = (donation_window.winfo_screenwidth() // 2) - (width // 2)
    y = (donation_window.winfo_screenheight() // 2) - (height // 2)
    donation_window.geometry(f"{width}x{height}+{x}+{y}")

def create_about_dialog(root, version):
    from utils.config import GITHUB_CONFIG
    """显示关于对话框"""
    about_text = (
        f"抖音直播推流地址获取工具\n"
        f"版本：{version}\n"
        f"作者：关水来了\n\n"
        f"GitHub：{GITHUB_CONFIG['REPO_URL']}\n\n"
        f"本工具仅供学习交流使用"
    )
    messagebox.showinfo("关于", about_text)
