import requests
from tkinter import messagebox
import webbrowser
from .config import VERSION, GITHUB_CONFIG

def check_for_updates():
    try:
        response = requests.get(GITHUB_CONFIG["API_URL"], timeout=5)
        if response.status_code == 200:
            latest_release = response.json()
            latest_version = latest_release['tag_name']
            # 获取更新说明
            release_notes = latest_release.get('body', '暂无更新说明')

            if latest_version != VERSION:
                if messagebox.askyesno(
                    "发现新版本",
                    f"当前版本: {VERSION}\n"
                    f"最新版本: {latest_version}\n\n"
                    f"更新内容:\n{release_notes}\n\n"
                    "是否前往下载页面更新？"
                ):
                    webbrowser.open(GITHUB_CONFIG["DOWNLOAD_URL"])
                    return True
    except Exception as e:
        print(f"检查更新失败: {str(e)}")
    return False
