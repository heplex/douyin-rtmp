chcp 65001 >nul

@echo off
setlocal enabledelayedexpansion

:: 检查并显示 Python 环境信息
echo 正在检查 Python 环境...
echo ----------------------------------------

python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [错误] Python 未安装或未添加到环境变量！
    echo 请安装 Python 并确保其已添加到系统环境变量中。
    pause
    exit /b 1
) else (
    echo [Python 版本]
    python --version
    echo [Python 路径]
    where python
)

:: 检查并显示 pip 信息
pip --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [错误] pip 未安装或未正确配置！
    echo 请确保 pip 已正确安装。
    pause
    exit /b 1
) else (
    echo [pip 版本]
    pip --version
)

echo ----------------------------------------
echo Python 环境检查通过！
echo ----------------------------------------

:: 检查是否需要跳过确认
set "skip_confirm="
set "use_nuitka="
for %%a in (%*) do (
    if "%%a"=="-y" set "skip_confirm=1"
    if "%%a"=="-yes" set "skip_confirm=1"
    if "%%a"=="nuitka" set "use_nuitka=1"
)

:: 添加确认步骤
if not defined skip_confirm (
    set /p "confirm=是否继续安装依赖并执行打包操作？(Y/N): "
    if /i not "!confirm!"=="Y" (
        echo 操作已取消。
        pause
        exit /b 0
    )
)

:: 检查打包方式
if defined use_nuitka (
    echo 使用 Nuitka 进行打包...
    
    :: 创建 nuitka 输出目录
    if not exist "nuitka_out" mkdir nuitka_out
    
    :: 安装必要的包
    echo 正在安装依赖包...
    pip install -r requirements.txt
    pip install ordered-set zstandard nuitka
    
    :: Nuitka 打包命令
    nuitka --mingw64 --standalone --onefile --follow-imports ^
    --show-memory --show-progress --assume-yes-for-downloads ^
    --windows-uac-admin --windows-console-mode=disable ^
    --windows-icon-from-ico=assets/logo.ico --lto=yes ^
    --enable-plugin=tk-inter ^
    --include-data-files=assets/=assets/=* ^
    --include-data-files=resources/=resources/=* ^
    --output-dir=nuitka_out ^
    --output-filename=douyin-rtmp-nuitka.exe main.py
) else (
    echo 使用 PyInstaller 进行打包...
    
    :: 安装必要的包
    pip install -r requirements.txt
    pip install pyinstaller
    
    :: PyInstaller 打包命令
    pyinstaller --onefile --uac-admin --noconsole ^
    --icon=assets/logo.ico ^
    --add-data="resources;resources" ^
    --add-data="assets;assets" ^
    --name=douyin-rtmp main.py
)

echo 打包完成！
pause