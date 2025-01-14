import os
import sys
import webbrowser
from tkinter import messagebox

class NpcapManager:
    def __init__(self, logger):
        self.logger = logger
        """获取资源文件的绝对路径，兼容开发、Nuitka打包和PyInstaller打包后的环境"""
        if hasattr(sys, '_MEIPASS'):
            # 在PyInstaller打包后的环境中
            application_path = sys._MEIPASS
        else:
            # 在Nuitka打包后的环境或开发环境中
            application_path = os.path.dirname(os.path.dirname(__file__))

        self.installer_path = os.path.join(application_path, "resources", "npcap-1.80.exe")
        self.logger.info(f"Npcap安装程序路径: {self.installer_path}")

        # 添加路径检查日志
        self.logger.info(f"当前文件路径: {__file__}")
        self.logger.info(f"项目根目录: {application_path}")
        if os.path.exists(self.installer_path):
            self.logger.info("找到Npcap安装程序")
        else:
            self.logger.info(f"未找到Npcap安装程序，请确认文件位置: {self.installer_path}")

    def check(self):
        """检查Npcap是否已安装"""
        try:
            import winreg
            winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\WOW6432Node\Npcap",
                0,
                winreg.KEY_READ
            )
            self.logger.info("检测到Npcap已安装")
            return True
        except WindowsError:
            self.logger.error("未检测到Npcap")
            return False

    def check_and_install(self):
        """检查并安装Npcap"""
        if self.check():
            return True

        response = messagebox.askquestion(
            "缺少必要组件",
            "检测到未安装Npcap，是否立即安装？\n(需要管理员权限)",
            icon='warning'
        )

        if response == 'yes':
            try:
                """获取资源文件的绝对路径，兼容开发、Nuitka打包和PyInstaller打包后的环境"""
                if hasattr(sys, '_MEIPASS'):
                    # 在PyInstaller打包后的环境中
                    application_path = sys._MEIPASS
                else:
                    # 在Nuitka打包后的环境或开发环境中
                    application_path = os.path.dirname(os.path.dirname(__file__))

                npcap_installer = os.path.join(application_path, "resources", "npcap-1.80.exe")

                if os.path.exists(npcap_installer):
                    self.logger.info(f"正在启动Npcap安装程序: {npcap_installer}")
                    os.startfile(npcap_installer)
                    messagebox.showinfo("提示", "请完成Npcap安装后重启程序")
                else:
                    self.logger.info(f"未找到Npcap安装程序: {npcap_installer}")
                    self.show_npcap_warning()
                sys.exit(0)
            except Exception as e:
                error_msg = f"安装Npcap失败: {str(e)}"
                self.logger.error(error_msg)
                messagebox.showerror("错误", error_msg)
                sys.exit(1)
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
                self.logger.info("正在启动Npcap卸载程序...")
                os.startfile(uninstaller)
                messagebox.showinfo("提示", "请完成Npcap卸载后重启程序")
                sys.exit(0)
            else:
                # 如果找不到卸载程序，打开控制面板
                self.logger.info("未找到Npcap卸载程序，正在打开控制面板...")
                os.system('control appwiz.cpl')
                messagebox.showinfo("提示",
                    "请在控制面板中找到并卸载Npcap，\n完成后重启程序。")

        except Exception as e:
            error_msg = f"卸载Npcap时出错: {str(e)}"
            self.logger.error(error_msg)
            messagebox.showerror("错误", error_msg)

    def install_npcap(self):
        """安装 Npcap"""
        try:
            self.logger.info(f"正在启动Npcap安装程序: {self.installer_path}")
            if os.path.exists(self.installer_path):
                os.startfile(self.installer_path)
                messagebox.showinfo("提示", "请完成Npcap安装后重启程序")
            else:
                self.logger.error(f"找不到Npcap安装程序：{self.installer_path}")
                self.show_npcap_warning()
        except Exception as e:
            self.logger.error(f"安装Npcap失败: {str(e)}")
            self.show_npcap_warning()