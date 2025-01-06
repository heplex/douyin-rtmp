from datetime import datetime
import tkinter as tk

class Logger:
    def __init__(self):
        self.console = None
        self.packet_console = None
        
    def set_consoles(self, console, packet_console):
        """设置日志输出控件"""
        self.console = console
        self.packet_console = packet_console
        
    def info(self, message):
        """输出普通日志"""
        if self.console:
            self._log_to_console(message)
            
    def packet(self, message):
        """输出数据包日志"""
        if self.packet_console:
            self._log_to_packet_console(message)
            
    def error(self, message):
        """输出错误日志"""
        if self.console:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self._log_to_console(f"[{current_time}] {message}")
        
    def _log_to_console(self, message):
        """向主控制台输出日志"""
        try:
            if not message.startswith('[20'):  # 如果消息不是以时间戳开头
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                message = f"[{current_time}] {message}"
            self.console.insert(tk.END, f"{message}\n")
            self.console.see(tk.END)
        except Exception as e:
            print(f"日志输出错误: {str(e)}")
        
    def _log_to_packet_console(self, message):
        """向数据包控制台输出日志"""
        try:
            self.packet_console.insert(tk.END, f"{message}\n")
            self.packet_console.see(tk.END)
            # 自动切换到数据包监控标签页
            if ">>> 发现" in message:
                if hasattr(self.packet_console.master, 'master'):
                    notebook = self.packet_console.master.master
                    if hasattr(notebook, 'select'):
                        notebook.select(self.packet_console.master)
        except Exception as e:
            print(f"数据包日志输出错误: {str(e)}")
        
    def clear_console(self):
        """清除主控制台内容"""
        if self.console:
            self.console.delete(1.0, tk.END)
            self.info("控制台已清除")
            
    def clear_packet_console(self):
        """清除数据包控制台内容"""
        if self.packet_console:
            self.packet_console.delete(1.0, tk.END)
            # 在数据包控制台显示清除提示
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.packet_console.insert(tk.END, f"[{current_time}] 数据包日志已清除\n")
            self.packet_console.see(tk.END) 