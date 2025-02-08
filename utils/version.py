import requests
from tkinter import messagebox
import webbrowser
from .config import VERSION, GITHUB_CONFIG

def check_for_updates():
    """
    检查更新
    Returns:
        tuple: (has_update, clicked_yes)
        - has_update: 是否存在更新
        - clicked_yes: 如果存在更新，用户是否点击了确认更新
    """
    try:
        response = requests.get(GITHUB_CONFIG["API_URL"], timeout=10)
        if response.status_code == 200:
            latest_release = response.json()
            latest_version = latest_release['tag_name']
            release_notes = latest_release.get('body', '暂无更新说明')
            update_suggestions = latest_release.get('update_suggestions', '暂无更新建议')

            if latest_version != VERSION:
                # 存在更新
                if messagebox.askyesno(
                    "发现新版本",
                    f"当前版本: {VERSION}\n"
                    f"最新版本: {latest_version}\n\n"
                    f"更新内容:\n{release_notes}\n\n"
                    f"更新建议:\n{update_suggestions}\n\n" 
                    "是否前往下载页面更新？"
                ):
                    webbrowser.open(GITHUB_CONFIG["DOWNLOAD_URL"])
                    return True, True  # 有更新，用户点击了是
                return True, False  # 有更新，用户点击了否
            return False, False  # 没有更新
    except Exception as e:
        print(f"检查更新失败: {str(e)}")
    return False, False  # 检查失败，视为没有更新
