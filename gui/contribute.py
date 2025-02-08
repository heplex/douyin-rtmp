import tkinter as tk
from tkinter import ttk
import json
import requests
from tkinter import messagebox

class ContributeDialog:
    def __init__(self, parent):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("贡献榜")
        self.dialog.geometry("500x400")
        self.dialog.resizable(False, False)
        
        # 配置样式
        style = ttk.Style()
        
        # 配置感谢语样式
        style.configure(
            "Thanks.TLabel",
            font=("微软雅黑", 11, "bold"),
            foreground="#ff6b6b",
            background="#f8f9fa"
        )
        
        # 配置标题和描述样式
        style.configure(
            "Description.TLabel",
            font=("微软雅黑", 10),
            foreground="#666666",
            background="#f8f9fa"
        )
        
        style.configure(
            "Title.TFrame",
            background="#f8f9fa"
        )
        
        # 配置Treeview样式
        style.configure(
            "Custom.Treeview.Heading",
            font=("微软雅黑", 10, "bold"),
            background="#e9ecef",
            foreground="#495057",
            relief="flat"
        )
        
        style.configure(
            "Custom.Treeview",
            font=("微软雅黑", 9),
            rowheight=30,
            background="#ffffff",
            fieldbackground="#ffffff",
            foreground="#333333",
            borderwidth=0
        )
        
        # 配置选项卡样式
        style.configure(
            "TNotebook.Tab",
            padding=[10, 5],
            font=("微软雅黑", 9)
        )
        
        # 移除Treeview的边框
        style.layout("Custom.Treeview", [
            ('Custom.Treeview.treearea', {'sticky': 'nswe'})
        ])
        
        # 使对话框居中
        self.center_dialog()
        
        # 创建主框架
        self.main_frame = ttk.Frame(self.dialog, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建选项卡控件
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # 加载数据
        self.load_contribute_data()
        
    def center_dialog(self):
        """使对话框在父窗口中居中"""
        self.dialog.transient(self.dialog.master)
        self.dialog.grab_set()
        
        # 获取父窗口位置和大小
        parent = self.dialog.master
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        
        # 计算居中位置
        dialog_width = 500
        dialog_height = 400
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        self.dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        
    def load_contribute_data(self):
        """加载贡献数据"""
        try:
            response = requests.get(
                "https://douyin-rtmp.config.clunk.cn/contribute.json"
            )
            data = response.json()
            self.create_tabs(data)
        except Exception as e:
            messagebox.showerror("错误", f"加载贡献数据失败: {str(e)}")
            self.dialog.destroy()
            
    def create_tabs(self, data):
        """创建选项卡"""
        for category in data:
            # 创建选项卡页面
            tab = ttk.Frame(self.notebook)
            self.notebook.add(tab, text=category["way"])
            
            # 创建标题框架
            title_frame = ttk.Frame(tab, style="Title.TFrame")
            title_frame.pack(fill=tk.X, padx=10, pady=(10, 0))
            
            # 添加感谢语
            thanks = ttk.Label(
                title_frame,
                text="感谢所有为项目做出贡献的人 ❤️",
                style="Thanks.TLabel"
            )
            thanks.pack(pady=(5, 5), anchor=tk.W)
            
            # 添加描述标签
            description = ttk.Label(
                title_frame, 
                text=category["description"], 
                wraplength=460,
                justify=tk.LEFT,
                style="Description.TLabel"
            )
            description.pack(pady=(0, 10), anchor=tk.W)
            
            # 创建分隔线
            separator = ttk.Separator(tab, orient="horizontal")
            separator.pack(fill=tk.X, padx=10, pady=(0, 10))
            
            # 创建Treeview和滚动条
            tree_frame = ttk.Frame(tab)
            tree_frame.pack(fill=tk.BOTH, expand=True, padx=10)
            
            # 创建垂直滚动条
            vsb = ttk.Scrollbar(tree_frame, orient="vertical")
            vsb.pack(side=tk.RIGHT, fill=tk.Y)
            
            # 创建Treeview
            tree = ttk.Treeview(
                tree_frame,
                columns=("name", "things"),
                show="headings",
                height=12,
                selectmode="none",
                style="Custom.Treeview"
            )
            tree.pack(fill=tk.BOTH, expand=True)
            
            # 配置滚动条
            vsb.configure(command=tree.yview)
            tree.configure(yscrollcommand=vsb.set)
            
            # 设置列标题
            tree.heading("name", text="贡献者")
            tree.heading("things", text="贡献内容")
            
            # 设置列宽和属性
            tree.column("name", width=120, anchor=tk.W)
            tree.column("things", width=340, anchor=tk.W)
            
            # 添加数据并设置间隔色
            for i, staff in enumerate(category["staff"]):
                tree.insert(
                    "", 
                    tk.END, 
                    values=(staff["name"], staff["things"]),
                    tags=('oddrow' if i % 2 else 'evenrow',)
                )
            
            # 设置间隔行颜色
            tree.tag_configure('oddrow', background='#f5f5f5')
            tree.tag_configure('evenrow', background='#ffffff')
            
            # 禁用选中效果
            def remove_selection(event):
                tree.selection_remove(tree.selection())
            tree.bind("<<TreeviewSelect>>", remove_selection)