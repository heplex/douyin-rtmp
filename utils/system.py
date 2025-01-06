import os
import ctypes
import sys

def is_admin():
    """检查是否以管理员权限运行"""
    try:
        return os.getuid() == 0
    except AttributeError:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0

def get_resource_path(relative_path):
    """获取资源文件的绝对路径，支持开发环境和打包后的环境"""
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller 打包后的路径
        base_path = sys._MEIPASS
    else:
        # 开发环境下的路径
        base_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    
    return os.path.join(base_path, relative_path) 