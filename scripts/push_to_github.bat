@echo off
chcp 65001 >nul
echo ============================================================
echo 推送到GitHub
echo ============================================================
echo.

cd ..

echo [1/3] 验证GitHub CLI登录状态...
gh auth status
if errorlevel 1 (
    echo 错误: 未登录GitHub
    echo 请运行: gh auth login
    pause
    exit /b 1
)
echo.

echo [2/3] 创建GitHub仓库...
echo 仓库名: manga-organizer
echo 描述: 漫画收藏标准化整理工具 - 自动化整理、转换和标准化漫画文件
echo 可见性: public
echo.

gh repo create manga-organizer --public --source=. --description "漫画收藏标准化整理工具 - 自动化整理、转换和标准化漫画文件的Python工具，支持日漫、美漫、港漫和连环画" --push

if errorlevel 1 (
    echo.
    echo 注意: 如果仓库已存在，将只推送代码
    echo.
    echo [3/3] 添加远程仓库并推送...

    REM 尝试添加远程仓库
    git remote add origin https://github.com/xbfool/manga-organizer.git 2>nul

    REM 设置主分支为main
    git branch -M main

    REM 推送代码
    git push -u origin main
)

echo.
echo ============================================================
echo ✓ 推送完成！
echo.
echo GitHub仓库地址:
echo https://github.com/xbfool/manga-organizer
echo.
echo 下一步:
echo   1. 访问仓库查看README
echo   2. 添加Topics标签
echo   3. 邀请协作者（如需要）
echo ============================================================
pause
