# 抖音直播推流地址获取工具

一款基于python3.12开发、Npcap进行网络抓包的抖音直播推流地址获取工具
获取到推流地址后，可以通过obs等直播工具进行抖音直播

## 使用说明

### 使用环境
Windows 10 及以上版本，低版本Windows未进行验证过，也许可行？
需关闭杀毒软件或加入白名单

### 使用说明

1. 本工具使用了网络抓包技术，可能会被杀毒软件误报，在下载时请关闭所有的杀毒软件或将本软件加入到白名单中，如360、腾讯管家、火绒、windows defender等;
2.  下载方式
    1.  在[Releases](https://github.com/heplex/douyin-rtmp/releases)页面下载最新版本的抖音直播推流地址获取工具；
    2.  直接下载本仓库中的`dist/main.exe`，一般此处为最新版本；
3. 下载完成后，使用管理员权限进行运行；
4. 在弹出的免责声明对话框中，点击“确定”按钮，继续使用则表示您同意以上条款；
5. 如果未检测到Npcap，会提示先安装Npcap，安装完成后，重新启动软件；
6. 选择对应的网络接口，有线网卡优先，如果未检测到，请手动选择；
7. 点击“开始捕获”按钮，开始捕获抖音直播推流地址；
8. 打开直播伴侣进行开播，推流地址会自动获取，并显示在软件中；
9.  如果推流地址获取失败，请检查网络接口是否选择正确，以及直播伴侣是否正常开播；
10. 如果仍然失败，可以尝试在工具重新安装Npcap，并重新启动软件；

### 卸载

1. 在工具选项下，点击卸载Npcap，卸载完成后，删除本软件即可；



## 免责说明

1. 本工具仅供学习和研究使
2. 请勿用于任何商业用途
3. 使用本工具产生的一切后果由使用者自行承担
4. 本工具使用了网络抓包技术，可能会被杀毒软件误报
   这是因为抓包功能与某些恶意软件行为类似，请放心使用

## 界面展示

### 使用界面

![使用界面](./images/使用界面.png)

## 更新日志

1. 2025.01.06 v1.0.0 
   1. 更新获取推流地址以及推流功能
2. 2025.01.06 v1.0.1 
   1. 重构代码，调整项目结构
   2. 优化界面操作逻辑以及界面布局
   3. 优化抓包匹配正则
   4. 增加更新检测
   5. 优化Npcap安装


## 开发指南

### 目录结构

project
├── main.py                # 主入口
├── resources
│   └── npcap-1.80.exe    # Npcap安装程序
├── core
│   ├── capture.py        # 数据包捕获
│   └── npcap.py          # Npcap管理
├── gui
│   ├── main_window.py    # 主窗口
│   └── widgets.py        # GUI组件
└── utils
    ├── logger.py         # 日志管理
    ├── network.py        # 网络接口
    └── system.py         # 系统工具


### 项目启动
```
pip install -r requirements.txt && python main.py
```

### 打包命令
```
pyinstaller --onefile --uac-admin --icon=assets/logo.ico --add-data="resources;resources" --add-data="assets;assets" --noconsole main.py
```



## Star History

<a href="https://star-history.com/#heplex/douyin-rtmp&Date">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=heplex/douyin-rtmp&type=Date&theme=dark" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=heplex/douyin-rtmp&type=Date" />
   <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=heplex/douyin-rtmp&type=Date" />
 </picture>
</a>

