import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import requests
import webbrowser
from utils.config import GITHUB_CONFIG
from utils.content_config import ADVERTISEMENT_TEXT
from utils.resource import resource_path


class AdPanel:
    def __init__(self, parent):
        """
        初始化广告面板

        Args:
            parent: 父级窗口/框架
        """
        self.parent = parent
        self.create_ad_panel()

    def create_ad_panel(self):
        """创建广告面板"""
        self.ad_frame = ttk.LabelFrame(self.parent, text="联系我", padding="5")
        self.ad_frame.grid(
            row=1, column=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5, padx=5
        )
        self.ad_frame.columnconfigure(0, weight=1)

        try:
            self._setup_github_icon()
        except Exception:
            self._setup_fallback_link()

        self._setup_ad_text()

    def _setup_github_icon(self):
        """设置GitHub图标和链接"""
        github_icon = tk.PhotoImage(file=resource_path("assets/github.png"))

        # 创建图标标签
        logo_label = ttk.Label(self.ad_frame, image=github_icon, cursor="hand2")
        logo_label.image = github_icon
        logo_label.grid(row=0, column=0, pady=(5, 2), padx=5)
        logo_label.bind("<Button-1>", lambda e: self.open_github())

        # 缩放图标
        github_icon = github_icon.subsample(4, 4)
        logo_label.configure(image=github_icon)
        logo_label.image = github_icon

        # 添加仓库链接
        repo_label = ttk.Label(
            self.ad_frame,
            text=GITHUB_CONFIG["REPO_URL"],
            cursor="hand2",
            foreground="blue",
            font=("", 9, "underline"),
        )
        repo_label.grid(row=1, column=0, pady=(0, 5), padx=5)
        repo_label.bind("<Button-1>", lambda e: self.open_github())

    def _setup_fallback_link(self):
        """设置备用文本链接"""
        link_label = ttk.Label(
            self.ad_frame,
            text=GITHUB_CONFIG["REPO_URL"],
            cursor="hand2",
            foreground="blue",
        )
        link_label.grid(row=0, column=0, pady=5, padx=5)
        link_label.bind("<Button-1>", lambda e: self.open_github())

    def _setup_ad_text(self):
        """设置广告文本区域"""
        self.ad_text = scrolledtext.ScrolledText(
            self.ad_frame, wrap=tk.WORD, width=20, height=15
        )
        self.ad_text.grid(
            row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5, padx=5
        )

        # 显示默认广告内容
        self.ad_text.insert(tk.END, ADVERTISEMENT_TEXT)
        self.ad_text.configure(state="disabled")

        # 添加右键菜单
        self.context_menu = tk.Menu(self.ad_text, tearoff=0)
        self.context_menu.add_command(label="复制", command=self._copy_text)
        self.ad_text.bind("<Button-3>", self._show_context_menu)

    def _copy_text(self):
        """复制选中的文本"""
        try:
            self.ad_text.configure(state="normal")
            selected_text = self.ad_text.selection_get()
            self.parent.clipboard_clear()
            self.parent.clipboard_append(selected_text)
        except:
            self.parent.clipboard_clear()
            self.parent.clipboard_append(self.ad_text.get(1.0, tk.END))
        finally:
            self.ad_text.configure(state="disabled")

    def _show_context_menu(self, event):
        """显示右键菜单"""
        self.context_menu.tk_popup(event.x_root, event.y_root)

    def async_fetch_ad_content(self):
        """异步获取广告内容"""

        def fetch_content():
            try:
                response = requests.get(
                    "https://douyin-rtmp.config.clunk.cn/ads",
                    timeout=5,
                )
                if response.status_code == 200:
                    self.parent.after(0, self.update_ad_content, response.text)
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

    def open_github(self):
        """打开GitHub页面"""
        webbrowser.open(GITHUB_CONFIG["REPO_URL"])
