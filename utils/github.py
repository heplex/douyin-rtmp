import re
import requests
from utils.logger import Logger

class GithubAPI:
    def __init__(self):
        self.logger = Logger()
        
    def get_latest_version(self, release_url):
        """
        从GitHub release页面获取最新版本号
        
        Args:
            release_url: GitHub releases页面地址，如 https://github.com/user/repo/releases
            
        Returns:
            str: 最新版本号，格式如 v1.0.0，获取失败返回"未知"
        """
        try:
            # 从URL中提取用户名和仓库名
            pattern = r"github\.com/([^/]+)/([^/]+)"
            match = re.search(pattern, release_url)
            if not match:
                self.logger.error(f"无效的GitHub URL: {release_url}")
                return "未知"
                
            owner, repo = match.groups()
            repo = repo.replace('releases', '').strip('/')
            
            # 调用GitHub API获取最新release
            api_url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
            headers = {
                'Accept': 'application/vnd.github.v3+json',
            }
            
            response = requests.get(api_url, headers=headers)
            response.raise_for_status()
            
            release_data = response.json()
            version = release_data.get('tag_name', '未知')
            
            return version
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"请求GitHub API失败: {str(e)}")
            return "未知"
        except Exception as e:
            self.logger.error(f"获取最新版本失败: {str(e)}")
            return "未知" 