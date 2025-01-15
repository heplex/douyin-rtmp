import tkinter as tk
from tkinter import ttk
import json
import os
import requests
from utils.logger import Logger
from utils.github import GithubAPI
from utils.obs import OBSUtils
from tkinter import messagebox


class PluginManagerFrame(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.logger = Logger()
        self.github_api = GithubAPI()
        self.obs_utils = OBSUtils()

        # 添加插件数据作为类属性
        self.plugin_data = {
            "plugins": [
                {
                    "pluginName": "obs-multi-rtmp",
                    "description": "多路推流工具,安装后在停靠窗口->多路推流勾选",
                    "releaseUrl": "https://github.com/sorayuki/obs-multi-rtmp/releases",
                    "installType": "1",
                    "suffix": "zip",
                    "installName": "obs-multi-rtmp",
                }
            ]
        }

        # 设置窗口大小和属性
        self.master.resizable(False, False)  # 禁止调整大小
        self.master.title("插件管理")  # 设置窗口标题

        # 设置样式
        self.style = ttk.Style()
        self.style.configure("Treeview", font=("微软雅黑", 9), rowheight=30)  # 设置行高
        self.style.configure(
            "Treeview.Heading", font=("微软雅黑", 9, "bold"), padding=(5, 5)
        )  # 设置表头样式

        # 创建主框架
        main_frame = ttk.Frame(self)
        main_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # 创建标题标签
        title_label = ttk.Label(
            main_frame, text="OBS 插件管理", font=("微软雅黑", 12, "bold")
        )
        title_label.pack(pady=(0, 10))

        # 创建表格框架
        table_frame = ttk.Frame(main_frame)
        table_frame.pack(fill=tk.BOTH, expand=True)

        # 创建表格
        self.create_table(table_frame)

        # 加载插件数据
        self.load_plugins()

        # 设置固定窗口大小
        self.master.update()
        self.master.minsize(600, 400)
        self.master.maxsize(600, 400)

    def create_table(self, parent):
        """创建插件列表表格"""
        # 创建表格
        columns = ("name", "description", "status", "action")
        self.tree = ttk.Treeview(parent, columns=columns, show="headings", height=10)

        # 设置列标题
        self.tree.heading("name", text="插件名称")
        self.tree.heading("description", text="描述")
        self.tree.heading("status", text="状态")
        self.tree.heading("action", text="操作")

        # 设置列宽且禁止调整
        self.tree.column("name", width=100, anchor="w", stretch=False)
        self.tree.column(
            "description", width=300, anchor="w", stretch=False
        )  # 增加描述列宽度
        self.tree.column("status", width=100, anchor="center", stretch=False)
        self.tree.column("action", width=80, anchor="center", stretch=False)

        # 添加滚动条
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # 布局
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # 设置网格权重
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(0, weight=1)

        # 绑定点击事件
        self.tree.bind("<Double-1>", self.on_item_double_click)
        self.tree.bind("<Motion>", self.show_tooltip)  # 添加鼠标移动事件
        self.tree.bind("<Leave>", self.hide_tooltip)  # 添加鼠标离开事件
        self.tree.bind("<Button-1>", self.on_click)  # 修改单击事件处理所有点击

        # 创建工具提示
        self.tooltip = None

        # 设置交替行颜色
        self.tree.tag_configure("oddrow", background="#F5F5F5")
        self.tree.tag_configure("evenrow", background="#FFFFFF")

    def load_plugins(self):
        """加载插件数据"""
        try:
            # TODO: 这里替换为实际的插件配置地址
            # response = requests.get('plugin_config_url')
            # self.plugin_data = response.json()

            # 清空现有数据
            for item in self.tree.get_children():
                self.tree.delete(item)

            # 遍历插件数据
            for plugin in self.plugin_data["plugins"]:
                # 获取插件状态
                status = self.obs_utils.check_plugin_status(plugin["installName"])

                # 根据状态设置操作按钮文本
                action = "卸载" if status == "已安装" else "安装"

                # 插入数据
                self.tree.insert(
                    "",
                    "end",
                    values=(
                        plugin["pluginName"],
                        plugin["description"],
                        status,
                        action,
                    ),
                )

            # 添加交替行颜色
            for index, item in enumerate(self.tree.get_children()):
                tag = "evenrow" if index % 2 == 0 else "oddrow"
                self.tree.item(item, tags=(tag,))

        except Exception as e:
            self.logger.error(f"加载插件数据失败: {str(e)}")

    def on_item_double_click(self, event):
        """处理双击事件"""
        item = self.tree.selection()[0]
        column = self.tree.identify_column(event.x)

        # 如果点击的是操作列
        if column == "#5":  # 第5列是操作列
            values = self.tree.item(item)["values"]
            plugin_name = values[0]
            action = values[4]

            if action == "安装":
                self.install_plugin(plugin_name)
            elif action == "重新安装":
                self.reinstall_plugin(plugin_name)

    def install_plugin(self, plugin_name):
        """安装插件"""
        plugin_config = self.get_plugin_config(plugin_name)
        if plugin_config:
            if self.obs_utils.install_plugin(plugin_config):
                self.logger.info(f"插件 {plugin_name} 安装成功")
                self.load_plugins()  # 刷新插件列表
            else:
                from tkinter import messagebox

                messagebox.showerror("错误", f"插件 {plugin_name} 安装失败")

    def reinstall_plugin(self, plugin_name):
        """重新安装插件"""
        self.install_plugin(plugin_name)

    def show_tooltip(self, event):
        """显示工具提示"""
        item = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)

        if item and column in ("#1", "#2", "#3"):  # 仅为名称、描述和版本列显示提示
            # 获取单元格文本
            column_id = int(column[1]) - 1
            cell_value = self.tree.item(item)["values"][column_id]

            # 创建工具提示
            if self.tooltip:
                self.tooltip.destroy()

            x, y, _, _ = self.tree.bbox(item, column)
            x += self.tree.winfo_rootx()
            y += self.tree.winfo_rooty()

            self.tooltip = tk.Toplevel(self)
            self.tooltip.wm_overrideredirect(True)
            self.tooltip.wm_geometry(f"+{x}+{y+20}")

            label = ttk.Label(
                self.tooltip,
                text=cell_value,
                background="#FFFFDD",
                relief="solid",
                borderwidth=1,
            )
            label.pack()

    def hide_tooltip(self, event):
        """隐藏工具提示"""
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

    def on_click(self, event):
        """处理单击事件"""
        item = self.tree.identify_row(event.y)
        if not item:
            return

        column = self.tree.identify_column(event.x)

        if column == "#4":  # 操作列
            values = self.tree.item(item)["values"]
            plugin_name = values[0]
            action = values[3]  # 获取操作类型（安装/卸载）

            # 创建确认对话框
            from tkinter import messagebox

            plugin_config = self.get_plugin_config(plugin_name)
            if plugin_config:
                if action == "卸载":
                    confirm = messagebox.askyesno(
                        "卸载确认",
                        f"确定要卸载 {plugin_name} 吗？\n\n"
                        f"插件描述：{plugin_config.get('description', '无描述')}",
                    )

                    if confirm:
                        self.uninstall_plugin(plugin_name)
                else:
                    # 安装逻辑保持不变
                    latest_version = self.github_api.get_latest_version(
                        plugin_config["releaseUrl"]
                    )
                    confirm = messagebox.askyesno(
                        "安装确认",
                        f"确定要{action} {plugin_name} ({latest_version}) 吗？\n\n"
                        f"插件描述：{plugin_config.get('description', '无描述')}",
                    )

                    if confirm:
                        self.install_plugin(plugin_name)

        elif column == "#3":  # 版本列
            values = self.tree.item(item)["values"]
            plugin_name = values[0]
            plugin_config = self.get_plugin_config(plugin_name)
            if plugin_config and "releaseUrl" in plugin_config:
                import webbrowser

                webbrowser.open(plugin_config["releaseUrl"])

    def get_plugin_config(self, plugin_name):
        """获取插件配置"""
        for plugin in self.plugin_data["plugins"]:
            if plugin["pluginName"] == plugin_name:
                return plugin
        return None

    def on_action_click(self, event):
        """处理操作按钮点击"""
        item = self.tree.identify_row(event.y)
        if not item:
            return

        column = self.tree.identify_column(event.x)
        if column == "#4":  # action列
            values = self.tree.item(item)["values"]
            plugin_name = values[0]
            plugin_config = self.get_plugin_config(plugin_name)
            if plugin_config:
                if self.obs_utils.install_plugin(plugin_config):
                    self.refresh_plugin_list()  # 安装成功后刷新列表

    def uninstall_plugin(self, plugin_name):
        """卸载插件"""
        try:
            plugin_config = self.get_plugin_config(plugin_name)
            if not plugin_config:
                return False

            if self.obs_utils.uninstall_plugin(plugin_config):
                self.logger.info(f"插件 {plugin_name} 卸载成功")
                self.load_plugins()  # 刷新插件列表
                messagebox.showinfo("成功", f"插件 {plugin_name} 已成功卸载")
                return True
            else:
                raise Exception("卸载插件失败")

        except Exception as e:
            self.logger.error(f"卸载插件失败: {str(e)}")
            messagebox.showerror("错误", f"插件 {plugin_name} 卸载失败: {str(e)}")
            return False
