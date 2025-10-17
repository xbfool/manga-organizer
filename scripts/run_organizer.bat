@echo off
chcp 65001 >nul
echo ============================================================
echo 漫画整理工具 - 开始整理
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
echo 启动漫画整理工具...
echo.
cd ..
python src\manga_organizer.py

echo.
echo ============================================================
echo 整理完成！
echo 查看日志: manga_organizer.log
echo 查看报告: manga_final_report.json
echo ============================================================
pause
