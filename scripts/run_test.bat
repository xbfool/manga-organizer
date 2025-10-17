@echo off
chcp 65001 >nul
echo ============================================================
echo 漫画整理工具 - 环境测试
echo ============================================================
echo.

set CONDA_PATH=C:\Users\xbfoo\miniconda3
set ENV_NAME=manga

echo 激活Conda环境 '%ENV_NAME%'...
call "%CONDA_PATH%\Scripts\activate.bat" %ENV_NAME%
if errorlevel 1 (
    echo 错误: 激活环境失败
    echo 请先运行 setup_environment.bat 创建环境
    pause
    exit /b 1
)

echo.
echo 运行环境检查脚本...
cd ..
python src\test_environment.py

echo.
echo ============================================================
pause
