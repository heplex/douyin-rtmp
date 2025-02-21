# 应用程序文本内容配置

# 广告位文本
ADVERTISEMENT_TEXT = """
如果觉得好用\n请给项目点个star，谢谢！\n\n
交流QQ群：870101332
"""

# 使用说明文本
HELP_TEXT = """使用说明：

1. 确保已安装 Npcap（如未安装可点击【工具】菜单进行安装）
2. 选择正确的网络接口（通常是当前正在使用的网络连接）有时候会状态错误都显示未连接，只要选择的网卡在数据包监控有数据，就说明是正确的
3. 打开抖音直播伴侣
4. 点击【开始捕获】按钮
5. 在直播伴侣中进行开播操作
6. 等待程序自动获取推流地址
7. 获取到地址后会自动停止捕获
8. 点击地址框后的【复制】按钮即可复制地址

注意事项：
· 请确保选择正确的网络接口
· 如果长时间未获取到地址，可以尝试停止后重新开始捕获
· 如遇问题请查看控制台输出的错误信息
· 本工具使用了网络抓包技术，可能会被杀毒软件误报
  这是因为抓包功能与某些恶意软件行为类似
  本工具完全开源，源代码可在 GitHub 查看，请放心使用"""

# OBS使用说明文本
OBS_HELP_TEXT = """OBS管理面板使用说明：

1. OBS路径配置
   · 点击后选择OBS安装目录下的obs64.exe文件
   · 配置成功后状态会显示"已配置"

2. 推流配置
   · 点击后选择OBS配置文件夹中的service.json文件
   · 文件位置：
     用户目录/AppData/Roaming/obs-studio/basic/profiles/
   · 一般只有一个文件夹，多个的情况下请自行区分，点进去以后
      选择service.json文件
   · 配置成功后状态会显示"已配置"

3. 同步推流码
   · 需要先完成OBS路径配置
   · 点击后会自动同步推流码到OBS配置文件中

4. 启动OBS
   · 需要先完成OBS路径配置
   · 点击后会自动启动OBS程序
   · 已经获取推流码的情况下会自动进行同步推流码

5. 插件管理
   · 点击后会打开插件管理面板
   · 仅可安装和卸载插件列表所支持插件
   · 一般采用压缩包形式安装，安装后需重启obs
   · 如果有好用的插件，可以进群里反馈，加到列表中
   · 不会使用的话，请加群与群友自行交流讨论
   · to插件作者：如果不喜欢自己的插件在列表中，可以联系删除

6. 注意事项
   · 首次使用请先配置OBS路径
   · 确保OBS已正确安装并运行过
   · 所有配置会自动保存，下次启动软件时自动加载
   
   """
