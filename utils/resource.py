import os
import sys

def resource_path(relative_path):
    """获取资源文件的绝对路径，兼容开发、Nuitka打包和PyInstaller打包后的环境"""
    if hasattr(sys, "_MEIPASS"):
        # 在PyInstaller打包后的环境中
        base_path = sys._MEIPASS
    else:
        # 在Nuitka打包后的环境或开发环境中
        base_path = os.path.dirname(os.path.dirname(__file__))

    return os.path.join(base_path, relative_path) 