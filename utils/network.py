from scapy.arch.windows import get_windows_if_list
import subprocess

class NetworkInterface:
    def __init__(self, logger):
        self.logger = logger
        self.interfaces = []
        
    def load_interfaces(self):
        """加载网络接口列表"""
        try:
            self.interfaces = get_windows_if_list()
            
            if self.interfaces:
                # 获取接口状态
                netsh_output = subprocess.check_output(
                    "netsh interface show interface",
                    shell=True
                ).decode('gbk', errors='ignore')
                
                active_interfaces = []
                inactive_interfaces = []
                default_interface = None
                
                # 解析 netsh 输出获取接口状态
                interface_status = {}
                for line in netsh_output.split('\n')[3:]:
                    if line.strip():
                        parts = line.strip().split()
                        if len(parts) >= 4:
                            status = parts[0]
                            name = ' '.join(parts[3:])
                            interface_status[name] = status == "已启用"
                
                for iface in self.interfaces:
                    name = iface['name']
                    desc = iface['description']
                    ip_addresses = iface.get('ips', [])
                    
                    # 从 netsh 结果获取状态
                    is_active = interface_status.get(name, False)
                    status = "已连接" if is_active else "未连接"
                    
                    # 格式化显示名称
                    display_name = f"[{status}] {name} - {desc[:47] + '...' if len(desc) > 50 else desc}"
                    
                    # 分类接口
                    if is_active and ip_addresses:
                        active_interfaces.append((display_name, name, desc))
                        # 检查是否为以太网
                        if "ethernet" in desc.lower() or "以太网" in desc:
                            default_interface = display_name
                    else:
                        inactive_interfaces.append((display_name, name, desc))
                    
                    # 打印详细信息到日志
                    self.logger.info(
                        f"接口: {name}\n"
                        f"   描述: {desc}\n"
                        f"   状态: {status}\n"
                        f"   IP地址: {', '.join(ip_addresses) if ip_addresses else '无'}\n"
                    )
                
                # 合并列表，活动接口在前
                interface_list = [x[0] for x in active_interfaces] + [x[0] for x in inactive_interfaces]
                
                self.logger.info(f"\n共找到 {len(self.interfaces)} 个网络接口")
                self.logger.info(f"其中活动接口 {len(active_interfaces)} 个")
                
                return {
                    'interfaces': interface_list,
                    'default': default_interface,
                    'active_count': len(active_interfaces)
                }
                
            else:
                self.logger.info("未找到可用的网络接口")
                return {
                    'interfaces': [],
                    'default': None,
                    'active_count': 0
                }
                
        except Exception as e:
            self.logger.error(f"加载网络接口失败: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return {
                'interfaces': [],
                'default': None,
                'active_count': 0
            } 