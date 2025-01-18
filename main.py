import tkinter as tk
from tkinter import messagebox
from gui.main_window import StreamCaptureGUI
from utils.system import is_admin

def main():
    # 检查是否以管理员权限运行
    if not is_admin():
        messagebox.showerror("错误", "请以管理员权限运行此程序！")
        return

    root = tk.Tk()
    StreamCaptureGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()