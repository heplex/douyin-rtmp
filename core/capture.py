from scapy.all import sniff, IP, TCP, Raw
import re
import threading
from datetime import datetime

class PacketCapture:
    def __init__(self, logger):
        self.logger = logger
        self.is_capturing = False
        self.capture_thread = None
        self.callbacks = []
        self.server_address = None
        self.stream_code = None
        
    def start(self, interface):
        """开始捕获数据包"""
        if self.is_capturing:
            return
            
        # 清空之前捕获的地址
        self.server_address = None
        self.stream_code = None
        
        self.is_capturing = True
        try:
            # 创建新的捕获线程
            self.capture_thread = threading.Thread(target=self._start_capture, args=(interface,))
            self.capture_thread.daemon = True
            self.capture_thread.start()
            self.logger.info(f"开始在接口 {interface} 上捕获数据包")
        except Exception as e:
            self.logger.error(f"启动捕获时发生错误: {str(e)}")
            self.is_capturing = False
        
    def stop(self):
        """停止捕获数据包"""
        if not self.is_capturing:
            return
            
        self.is_capturing = False
        if self.capture_thread and self.capture_thread.is_alive():
            # 不要尝试join当前线程
            if threading.current_thread() != self.capture_thread:
                self.capture_thread.join(timeout=1.0)
        self.capture_thread = None
        self.logger.info("停止捕获数据包")
        
    def add_callback(self, callback):
        """添加回调函数"""
        self.callbacks.append(callback)
        
    def _start_capture(self, interface):
        """实际的捕获过程"""
        try:
            sniff(iface=interface, 
                  prn=self._packet_callback, 
                  stop_filter=lambda x: not self.is_capturing)
        except Exception as e:
            self.logger.error(f"捕获过程中发生错误: {str(e)}")
            self.is_capturing = False
        
    def _packet_callback(self, packet):
        """处理捕获的数据包"""
        try:
            if IP in packet and TCP in packet and Raw in packet:
                # 记录基本连接信息
                src_ip = packet[IP].src
                dst_ip = packet[IP].dst
                src_port = packet[TCP].sport
                dst_port = packet[TCP].dport
                
                # 记录基本连接信息
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.logger.packet(
                    f"[{current_time}] {src_ip}:{src_port} -> {dst_ip}:{dst_port}"
                )
                
                try:
                    payload = packet[Raw].load.decode('utf-8', errors='ignore')
                    # 查找推流服务器地址
                    if 'connect' in payload:
                        # 修改正则表达式，排除特殊字符
                        server_match = re.search(r'(rtmp://[a-zA-Z0-9\-\.]+/[^/]+)', payload)
                        if server_match:
                            self.server_address = server_match.group(1).split('\x00')[0]  # 移除null字节
                            self.logger.info(f"\n>>> 找到推流服务器地址 <<<")
                            self.logger.info(f"地址: {self.server_address}")
                    
                    # 查找推流码 
                    if 'FCPublish' in payload:
                        code_match = re.search(r'(stream-\d+\?[a-zA-Z0-9_]+=[a-zA-Z0-9\-]+(?:&[a-zA-Z0-9_]+=[a-zA-Z0-9\-]+)*)', payload)
                        if code_match:
                            self.stream_code = code_match.group(1)
                            if self.stream_code.endswith('C'):
                                self.stream_code = self.stream_code[:-1]
                            self.logger.info(f"\n>>> 找到推流码 <<<")
                            self.logger.info(f"推流码: {self.stream_code}")
                    
                    # 当两个信息都获取到时，触发回调并停止捕获
                    if self.server_address and self.stream_code:
                        # 直接传递服务器地址和推流码两个参数
                        for callback in self.callbacks:
                            try:
                                callback(self.server_address, self.stream_code)
                            except Exception as e:
                                self.logger.error(f"执行回调函数时发生错误: {str(e)}")
                        
                    
                except UnicodeDecodeError:
                    pass  # 忽略无法解码的数据包
                    
                    
        except Exception as e:
            self.logger.error(f"处理数据包时发生错误: {str(e)}") 