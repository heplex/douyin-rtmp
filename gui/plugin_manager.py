import tkinter as tk
from tkinter import ttk
import requests
from utils.logger import Logger
from utils.github import GithubAPI
from utils.obs import OBSUtils
from tkinter import messagebox
import webbrowser


class PluginManagerFrame(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.logger = Logger()
        self.github_api = GithubAPI()
        self.obs_utils = OBSUtils()
        
        # 初始化插件数据
        self.plugin_data = None
        # 加载远程插件数据
        self.fetch_plugin_data()

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
            main_frame, text="OBS 插件管理（一般采用压缩包形式安装）", font=("微软雅黑", 12, "bold")
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

        self._button_cooldown = False  # 添加按钮状态标志

    def fetch_plugin_data(self):
        """从远程获取插件数据"""
        try:
            if self.plugin_data is None:  # 只在数据不存在时获取
                response = requests.get('https://gh-proxy.protoniot.com/heplex/douyin-rtmp/raw/config/config.json')
                self.plugin_data = response.json()
        except Exception as e:
            self.logger.error(f"获取插件数据失败: {str(e)}")
            # 使用默认数据作为备份
            self.plugin_data = {
                "plugins": [
                    {
                        "pluginName": "obs-multi-rtmp-dev",
                        "version": "0.6.0.1",
                        "description": "多路推流工具,安装后在停靠窗口->多路推流勾选",
                        "releaseUrl": "https://github.com/sorayuki/obs-multi-rtmp/releases",
                        "downloadUrl": "https://gh-proxy.protoniot.com/heplex/douyin-rtmp/raw/config/resources/obs-multi-rtmp-0.6.0.1-windows-x64.zip",
                        "installName": "obs-multi-rtmp"
                    }
                ]
            }

    def create_table(self, parent):
        """创建插件列表表格"""
        # 创建表格，添加version列
        columns = ("name", "description", "version", "status", "action")
        self.tree = ttk.Treeview(parent, columns=columns, show="headings", height=10)

        # 设置列标题
        self.tree.heading("name", text="插件名称")
        self.tree.heading("description", text="描述")
        self.tree.heading("version", text="版本")
        self.tree.heading("status", text="状态")
        self.tree.heading("action", text="操作")

        # 设置列宽且禁止调整
        self.tree.column("name", width=100, anchor="w", stretch=False)
        self.tree.column("description", width=220, anchor="w", stretch=False)
        self.tree.column("version", width=80, anchor="center", stretch=False)
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
        self.tree.bind("<Motion>", self.show_tooltip)  # 添加鼠标移动事件
        self.tree.bind("<Leave>", self.hide_tooltip)  # 添加鼠标离开事件
        self.tree.bind("<Button-1>", self.on_click)  # 修改单击事件处理所有点击

        # 创建工具提示
        self.tooltip = None

        # 设置交替行颜色
        self.tree.tag_configure("oddrow", background="#F5F5F5")
        self.tree.tag_configure("evenrow", background="#FFFFFF")

    def load_plugins(self):
        """加载插件数据到界面"""
        try:
            # 清空现有数据
            for item in self.tree.get_children():
                self.tree.delete(item)

            # 遍历插件数据
            for plugin in self.plugin_data["plugins"]:
                # 获取插件状态
                status = self.obs_utils.check_plugin_status(plugin["installName"])
                # 根据状态设置操作按钮文本
                action = "卸载" if status == "已安装" else "安装"

                # 插入数据，添加version字段
                self.tree.insert(
                    "",
                    "end",
                    values=(
                        plugin["pluginName"],
                        plugin["description"],
                        plugin["version"],
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


    def show_tooltip(self, event):
        """显示工具提示"""
        item = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)

        if item:
            values = self.tree.item(item)["values"]
            if not values:
                return

            # 创建工具提示
            if self.tooltip:
                self.tooltip.destroy()

            x = self.tree.winfo_rootx() + event.x
            y = self.tree.winfo_rooty() + self.tree.bbox(item, column)[1]

            self.tooltip = tk.Toplevel(self)
            self.tooltip.wm_overrideredirect(True)
            self.tooltip.wm_geometry(f"+{x}+{y+20}")

            # 根据不同列显示不同的提示内容
            tooltip_text = ""
            if column == "#1":  # 插件名称列
                tooltip_text = values[0]
            elif column == "#2":  # 描述列
                tooltip_text = values[1]
            elif column == "#3":  # 版本列
                current_version = values[2]
                plugin_name = values[0]
                plugin_config = self.get_plugin_config(plugin_name)
                if plugin_config and "releaseUrl" in plugin_config:
                    tooltip_text = f"当前版本: {current_version}\n点击查看最新版本"
            elif column == "#4":  # 状态列
                tooltip_text = values[3]
            elif column == "#5":  # 操作列
                tooltip_text = values[4]

            if tooltip_text:
                label = ttk.Label(
                    self.tooltip,
                    text=tooltip_text,
                    background="#FFFFDD",
                    relief="solid",
                    borderwidth=1,
                    wraplength=300  # 添加自动换行
                )
                label.pack()

    def hide_tooltip(self, event):
        """隐藏工具提示"""
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

    def on_click(self, event):
        """处理点击事件"""
        if self._button_cooldown:
            return

        item = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)
        
        if not item:
            return

        values = self.tree.item(item)["values"]
        if not values:
            return

        plugin_name = values[0]
        plugin_config = self.get_plugin_config(plugin_name)

        if column == "#5":  # 操作列
            self._button_cooldown = True
            self.tree.update()

            try:
                if values[4] == "安装":
                    if messagebox.askyesno("确认", f"确定要安装 {plugin_name} 吗？"):
                        success = self.obs_utils.install_plugin(plugin_config)
                        if success:
                            self.load_plugins()
                elif values[4] == "卸载":
                    if messagebox.askyesno("确认", f"确定要卸载 {plugin_name} 吗？"):
                        success = self.obs_utils.uninstall_plugin(plugin_config)
                        if success:
                            self.load_plugins()
            finally:
                self.after(1000, self._reset_button_cooldown)

        elif column == "#3" and plugin_config.get("releaseUrl"):  # 版本列
            webbrowser.open(plugin_config["releaseUrl"])

    def _reset_button_cooldown(self):
        """重置按钮冷却状态"""
        self._button_cooldown = False
        self.tree.update()

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
        if column == "#5": 
            values = self.tree.item(item)["values"]
            plugin_name = values[0]
            plugin_config = self.get_plugin_config(plugin_name)
            if plugin_config:
                if self.obs_utils.install_plugin(plugin_config):
                    self.load_plugins()  # 安装成功后刷新列表

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
