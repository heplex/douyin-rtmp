from scapy.arch.windows import get_windows_if_list
import subprocess
import traceback

class NetworkInterface:
    def __init__(self, logger):
        """
        初始化网络接口管理器
        @param logger: Logger实例
        """
        self.logger = logger

    def _get_interface_status(self):
        """获取网络接口状态"""
        try:
            # 使用 PowerShell 获取更详细的网络适配器状态
            ps_command = """
            Get-NetAdapter | Select-Object Name, Status, LinkSpeed, MediaConnectionState, InterfaceDescription | 
            ConvertTo-Csv -NoTypeInformation
            """
            ps_output = subprocess.check_output(
                ["powershell", "-Command", ps_command],
                stderr=subprocess.PIPE
            ).decode('utf-8', errors='ignore')
            
            # 获取 ipconfig 输出用于验证
            ipconfig_output = subprocess.check_output(
                "ipconfig /all",
                shell=True,
                stderr=subprocess.PIPE
            ).decode('gbk', errors='ignore')
            
            status_map = {}
            
            # 解析 ipconfig 输出获取媒体状态
            current_adapter = None
            media_states = {}
            for line in ipconfig_output.split('\n'):
                line = line.strip()
                if line.endswith(':'):
                    current_adapter = line[:-1].strip()
                elif '媒体状态' in line or 'Media State' in line:
                    is_disconnected = ('已断开' in line or 
                                     'disconnected' in line.lower() or 
                                     'Media disconnected' in line)
                    if current_adapter:
                        media_states[current_adapter] = not is_disconnected
            
            # 解析 PowerShell 输出
            for line in ps_output.split('\n')[1:]:  # 跳过标题行
                if line.strip():
                    parts = line.strip().strip('"').split('","')
                    if len(parts) >= 5:
                        name = parts[0]
                        adapter_status = parts[1]
                        link_speed = parts[2]
                        media_state = parts[3]
                        description = parts[4]
                        
                        # 检查是否为 VPN 适配器
                        is_vpn = any(vpn_keyword in description.lower() 
                                   for vpn_keyword in ['vpn', 'virtual', '虚拟'])
                        
                        # VPN适配器需要更严格的检查
                        if is_vpn:
                            # 对于VPN适配器，必须同时满足：
                            # 1. PowerShell 显示状态为 Up
                            # 2. ipconfig 显示媒体状态为已连接
                            is_active = (adapter_status == "Up" and 
                                       media_states.get(name, False))
                        else:
                            # 对于普通网卡，使用之前的判断逻辑
                            is_active = (
                                adapter_status == "Up" or 
                                (link_speed and link_speed != "0 bps")
                            )
                        
                        status_map[name] = is_active
            
            return status_map
        except subprocess.SubprocessError as e:
            self.logger.warning(f"获取接口状态失败: {str(e)}")
            return {}

    def _is_valid_ip(self, ip):
        """检查是否为有效的普通IP地址"""
        try:
            # 排除特殊IP地址
            if not ip or ':' in ip:  # 排除IPv6
                return False
            
            parts = ip.split('.')
            if len(parts) != 4:
                return False
            
            # 检查每个部分是否为0-255的数字
            if not all(part.isdigit() and 0 <= int(part) <= 255 for part in parts):
                return False
            
            # 排除特殊IP地址范围
            if (
                ip.startswith('0.') or      # 0.0.0.0/8
                ip.startswith('127.') or    # 127.0.0.0/8 (本地回环)
                ip.startswith('169.254.') or # 169.254.0.0/16 (链路本地)
                ip.startswith('224.') or    # 224.0.0.0/4 (组播地址)
                ip.startswith('240.') or    # 240.0.0.0/4 (保留地址)
                ip == '255.255.255.255'     # 广播地址
            ):
                return False
            
            return True
        except:
            return False

    def load_interfaces(self):
        """加载网络接口列表"""
        try:
            windows_interfaces = get_windows_if_list()
            interface_status = self._get_interface_status()
            
            active_interfaces = []
            inactive_interfaces = []
            default_interface = None

            for iface in windows_interfaces:
                try:
                    name = iface['name']
                    desc = iface.get('description', 'Unknown Description').strip() or 'Unknown Description'
                    ip_addresses = [
                        ip for ip in iface.get('ips', [])
                        if self._is_valid_ip(str(ip))
                    ]
                    
                    # 检查是否为VPN或虚拟适配器
                    is_vpn = any(vpn_keyword in desc.lower() 
                               for vpn_keyword in ['vpn', 'virtual', '虚拟'])
                    
                    # 对于VPN适配器，必须同时满足有效IP和接口状态为活动
                    if is_vpn:
                        is_active = bool(ip_addresses) and interface_status.get(name, False)
                    else:
                        is_active = bool(ip_addresses) or interface_status.get(name, False)
                    
                    display_desc = desc[:47] + '...' if len(desc) > 50 else desc
                    display_name = f"{name} [{'已连接' if is_active else '未连接'}] - {display_desc}"

                    if is_active:
                        active_interfaces.append(display_name)
                        # 不将VPN接口作为默认接口
                        if not default_interface and not is_vpn and ip_addresses and (
                            "ethernet" in desc.lower() or "以太网" in desc
                        ):
                            default_interface = display_name
                    else:
                        inactive_interfaces.append(display_name)

                    self.logger.info(
                        f"接口: {name}\n"
                        f"   描述: {desc}\n"
                        f"   类型: {'VPN/虚拟' if is_vpn else '物理'}\n"
                        f"   状态: {'已连接' if is_active else '未连接'}\n"
                        f"   有效IP地址: {', '.join(str(ip) for ip in ip_addresses) if ip_addresses else '无'}"
                    )
                except Exception as e:
                    self.logger.warning(f"处理接口 {iface['name']} 时出错: {str(e)}")
                    continue

            interface_list = active_interfaces + inactive_interfaces
            self.logger.info(f"\n共找到 {len(interface_list)} 个网络接口")
            self.logger.info(f"其中活动接口 {len(active_interfaces)} 个")

            return {
                'interfaces': interface_list,
                'default': default_interface,
                'active_count': len(active_interfaces)
            }
            
        except Exception as e:
            self.logger.error(f"加载网络接口失败: {str(e)}")
            self.logger.error(traceback.format_exc())
            return {'interfaces': [], 'default': None, 'active_count': 0}
