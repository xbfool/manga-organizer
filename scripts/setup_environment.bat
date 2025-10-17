@echo off
chcp 65001 >nul
echo ============================================================
echo 漫画整理工具 - 环境配置
echo ============================================================
echo.

set CONDA_PATH=C:\Users\xbfoo\miniconda3
set ENV_NAME=manga

echo [1/3] 检查Conda...
if not exist "%CONDA_PATH%\Scripts\conda.exe" (
    echo 错误: 未找到Conda，请检查路径
    pause
    exit /b 1
)
echo ✓ Conda已找到

echo.
echo [2/3] 创建Conda环境 '%ENV_NAME%'...
call "%CONDA_PATH%\Scripts\conda.exe" create -n %ENV_NAME% python=3.12 -y
if errorlevel 1 (
    echo 注意: 环境可能已存在，继续...
)

echo.
echo [3/3] 安装Python依赖包...
call "%CONDA_PATH%\Scripts\activate.bat" %ENV_NAME%
pip install rarfile
if errorlevel 1 (
    echo 错误: 安装依赖失败
    pause
    exit /b 1
)

echo.
echo ============================================================
echo ✓ 环境配置完成！
echo ============================================================
echo.
echo 环境名称: %ENV_NAME%
echo Python版本: 3.12
echo 已安装: rarfile
echo.
echo 下一步：
echo   1. 运行 run_test.bat 测试环境
echo   2. 运行 run_organizer.bat 开始整理漫画
echo.
pause
